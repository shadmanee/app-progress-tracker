#!/usr/bin/env python3
"""
phd_dump.py — minimal terminal viewer for the phd_tracker DB (no Flask needed)

Usage:
  python phd_dump.py <SQLALCHEMY_DB_URL> [--limit 20]

Examples:
  python phd_dump.py sqlite:///phd_tracker.db
  python phd_dump.py postgresql+psycopg2://user:pass@localhost:5432/phd_tracker --limit 10
"""

import sys
import argparse
from collections import defaultdict

from sqlalchemy import create_engine, MetaData, Table, select, text, func, distinct
from sqlalchemy.engine import Engine

def hr(title: str):
    print("\n" + "="*80)
    print(title)
    print("="*80)

def print_rows(rows, cols, limit):
    count = 0
    w = [max(len(str(c)), 8) for c in cols]
    for row in rows:
        count += 1
        if count == 1:
            print(" | ".join(str(c).ljust(w[i]) for i, c in enumerate(cols)))
            print("-+-".join("-"*w[i] for i in range(len(cols))))
        print(" | ".join(str(row[c]).ljust(w[i]) for i, c in enumerate(cols)))
        if limit and count >= limit:
            break
    if count == 0:
        print("(no rows)")
    else:
        print(f"... ({count} shown{' (capped)' if limit and count >= limit else ''})")

def load_tables(engine: Engine):
    md = MetaData()
    md.reflect(bind=engine)
    # Defensive: only pick tables we expect if present
    tables = {}
    for name in [
        "university", "department", "program",
        "professor", "professor_programs",
        "research_area", "professor_research_areas",
        "applicant"
    ]:
        if name in md.tables:
            tables[name] = md.tables[name]
    return tables

def print_counts(conn, tables):
    hr("Table counts")
    for name, tbl in tables.items():
        cnt = conn.execute(select(func.count())).scalar()
        print(f"{name:26s} {cnt}")

def sample_table(conn, tbl: Table, cols: list[str], title: str, limit: int):
    hr(title)
    sel_cols = [tbl.c[c] for c in cols if c in tbl.c]
    if not sel_cols:
        print("(columns not found)")
        return
    rows = conn.execute(select(*sel_cols).limit(limit)).mappings()
    print_rows(rows, cols, limit)

def dump_universities(conn, tables, limit):
    if "university" not in tables:
        return
    cols = ["id", "name", "city", "state", "country", "ranking_usnews"]
    sample_table(conn, tables["university"], cols, "Universities (sample)", limit)

def dump_departments(conn, tables, limit):
    if "department" not in tables:
        return
    cols = ["id", "name", "university_id"]
    sample_table(conn, tables["department"], cols, "Departments (sample)", limit)

def dump_programs(conn, tables, limit):
    if not {"program","department","university"}.issubset(tables):
        return
    hr("Programs → Department → University (+ distinct professor count)")
    program = tables["program"]
    dept = tables["department"]
    uni = tables["university"]
    pp = tables.get("professor_programs")

    # Group by (program.name, dept, uni); count DISTINCT professors if join table present
    sel = (
        select(
            program.c.name.label("program"),
            dept.c.name.label("department"),
            uni.c.name.label("university"),
            uni.c.city.label("city"),
            uni.c.state.label("state"),
            uni.c.country.label("country"),
            uni.c.ranking_usnews.label("ranking_usnews"),
        )
        .select_from(program.join(dept, program.c.department_id == dept.c.id)
                          .join(uni, dept.c.university_id == uni.c.id))
    )

    if pp is not None:
        sel = sel.add_columns(func.count(distinct(pp.c.professor_id)).label("prof_count")) \
                 .outerjoin(pp, pp.c.program_id == program.c.id) \
                 .group_by(program.c.name, dept.c.name, uni.c.name, uni.c.city, uni.c.state, uni.c.country, uni.c.ranking_usnews)
    else:
        sel = sel.add_columns(func.cast(0, program.c.id.type).label("prof_count")) \
                 .group_by(program.c.name, dept.c.name, uni.c.name, uni.c.city, uni.c.state, uni.c.country, uni.c.ranking_usnews)

    sel = sel.order_by(uni.c.name.asc(), dept.c.name.asc(), program.c.name.asc()).limit(limit)
    rows = conn.execute(sel).mappings()
    cols = ["program", "department", "university", "city", "state", "country", "ranking_usnews", "prof_count"]
    print_rows(rows, cols, limit)

def dump_professors(conn, tables, limit):
    if "professor" not in tables:
        return
    prof = tables["professor"]
    uni = tables.get("university")
    dept = tables.get("department")
    hr("Professors (basic info)")
    base_cols = [
        prof.c.id.label("id"),
        prof.c.name.label("name"),
        prof.c.title.label("title"),
        prof.c.email.label("email"),
        prof.c.hiring_status.label("hiring_status"),
        prof.c.contact_through.label("contact_through"),
    ]
    join = prof
    if dept is not None:
        base_cols.append(dept.c.name.label("department"))
        join = join.join(dept, prof.c.department_id == dept.c.id)
    if uni is not None:
        base_cols.append(uni.c.name.label("university"))
        base_cols.append(uni.c.city.label("city"))
        base_cols.append(uni.c.country.label("country"))
        join = join.join(uni, prof.c.university_id == uni.c.id)

    sel = select(*base_cols).select_from(join).order_by(prof.c.name.asc()).limit(limit)
    rows = conn.execute(sel).mappings()
    cols = [c.key for c in base_cols]
    print_rows(rows, cols, limit)

def dump_professor_programs(conn, tables, limit):
    # Aggregate programs and research areas per professor (comma-separated)
    if not {"professor"}.issubset(tables):
        return
    prof = tables["professor"]
    prog = tables.get("program")
    dept = tables.get("department")
    uni = tables.get("university")
    pp = tables.get("professor_programs")
    ra = tables.get("research_area")
    pra = tables.get("professor_research_areas")

    hr("Professors → Programs / Research Areas (aggregated)")

    # Build program list per professor
    prog_map = defaultdict(set)
    if pp is not None and prog is not None:
        prog_rows = conn.execute(
            select(pp.c.professor_id.label("prof_id"), prog.c.name.label("program_name"))
            .select_from(pp.join(prog, prog.c.id == pp.c.program_id))
        ).mappings()
        for r in prog_rows:
            prog_map[r["prof_id"]].add(r["program_name"])

    # Build research areas per professor
    ra_map = defaultdict(set)
    if pra is not None and ra is not None:
        ra_rows = conn.execute(
            select(pra.c.professor_id.label("prof_id"), ra.c.name.label("ra_name"))
            .select_from(pra.join(ra, ra.c.id == pra.c.research_area_id))
        ).mappings()
        for r in ra_rows:
            ra_map[r["prof_id"]].add(r["ra_name"])

    # Base professor info
    columns = [
        prof.c.id.label("id"),
        prof.c.name.label("name"),
        prof.c.title.label("title"),
    ]
    j = prof
    if dept is not None:
        columns.append(dept.c.name.label("department"))
        j = j.join(dept, prof.c.department_id == dept.c.id)
    if uni is not None:
        columns.append(uni.c.name.label("university"))
        j = j.join(uni, prof.c.university_id == uni.c.id)

    rows = conn.execute(select(*columns).select_from(j).order_by(prof.c.name.asc()).limit(limit)).mappings()

    # Print with aggregated lists
    cols = ["id", "name", "title", "department", "university", "programs", "research_areas"]
    print(" | ".join(c.ljust(16) for c in cols))
    print("-+-".join("-"*16 for _ in cols))
    shown = 0
    for r in rows:
        shown += 1
        programs = ", ".join(sorted(prog_map.get(r["id"], []))) or "-"
        ras = ", ".join(sorted(ra_map.get(r["id"], []))) or "-"
        out = {
            **r,
            "programs": programs,
            "research_areas": ras,
        }
        print(" | ".join(str(out.get(c, "")).ljust(16) for c in cols))
        if shown >= limit:
            break
    if shown == 0:
        print("(no rows)")
    else:
        print(f"... ({shown} shown{' (capped)' if shown >= limit else ''})")

def main():
    parser = argparse.ArgumentParser(description="Terminal viewer for phd_tracker DB (no frontend).")
    parser.add_argument("db_url", help="SQLAlchemy DB URL, e.g., sqlite:///phd_tracker.db")
    parser.add_argument("--limit", type=int, default=20, help="Max rows to print per section (default: 20)")
    args = parser.parse_args()

    engine = create_engine(args.db_url, future=True)
    tables = load_tables(engine)
    if not tables:
        print("No known tables found. Did you point to the right database?")
        sys.exit(1)

    with engine.connect() as conn:
        print(f"Connected to: {args.db_url}")
        print(f"Detected tables: {', '.join(sorted(tables.keys()))}")

        print_counts(conn, tables)
        dump_universities(conn, tables, args.limit)
        dump_departments(conn, tables, args.limit)
        dump_programs(conn, tables, args.limit)
        dump_professors(conn, tables, args.limit)
        dump_professor_programs(conn, tables, args.limit)

if __name__ == "__main__":
    main()
