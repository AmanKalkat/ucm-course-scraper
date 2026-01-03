from fastapi import FastAPI, status, HTTPException, Depends
from schemas import Course, CourseFilter
from typing import List, Optional
from database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import CourseModel


app = FastAPI()

# returns all courses with optional filters
@app.get("/courses", response_model=List[Course], status_code=status.HTTP_200_OK)
def get_courses(
    filters: CourseFilter = Depends(),
    db: Session = Depends(get_db)
):
    query = db.query(CourseModel)

    if filters.course_code:
        query = query.filter(CourseModel.course_code == filters.course_code)

    if filters.course_prefix:
        query = query.filter(CourseModel.course_code.like(f"{filters.course_prefix}%"))

    if filters.catalog_year:
        query = query.filter(CourseModel.catalog_year == filters.catalog_year)

    if filters.has_prereqs is not None:
        if filters.has_prereqs:
            query = query.filter(CourseModel._prereqs.isnot(None), CourseModel._prereqs != "")
        else:
            query = query.filter((CourseModel._prereqs.is_(None)) | (CourseModel._prereqs == ""))

    if filters.has_coreqs is not None:
        if filters.has_coreqs:
            query = query.filter(CourseModel._coreqs.isnot(None), CourseModel._coreqs != "")
        else:
            query = query.filter((CourseModel._coreqs.is_(None)) | (CourseModel._coreqs == ""))

    if filters.prereq_contains:
        query = query.filter(CourseModel._prereqs.like(f"%{filters.prereq_contains}%"))

    if filters.coreq_contains:
        query = query.filter(CourseModel._coreqs.like(f"%{filters.coreq_contains}%"))

    if filters.class_level:
        query = query.filter(CourseModel._class_levels.like(f"%{filters.class_level}%"))

    if filters.repeats_allowed is not None:
        if filters.repeats_allowed:
            query = query.filter(CourseModel.repeats_allowed_for_credit.isnot(None),
                                CourseModel.repeats_allowed_for_credit > 0)
        else:
            query = query.filter((CourseModel.repeats_allowed_for_credit.is_(None)) |
                                (CourseModel.repeats_allowed_for_credit == 0))

    if filters.min_repeat is not None:
        query = query.filter(CourseModel.repeats_allowed_for_credit >= filters.min_repeat)

    if filters.sort_by:
        sort_column = getattr(CourseModel, filters.sort_by, None)
        if sort_column is not None:
            query = query.order_by(sort_column)

    return query.all()

# returns all possible catalog years in the db
@app.get("/catalog_years", response_model=List[str], status_code=status.HTTP_200_OK)
def get_catalog_years(
    db: Session = Depends(get_db)
):
    catalog_years = db.query(CourseModel.catalog_year).distinct().order_by(CourseModel.catalog_year.desc()).all()
    return [year[0] for year in catalog_years]

# return all versions of the course (single course across all catalogs)
@app.get("/courses/code/{course_code}", response_model=List[Course], status_code=status.HTTP_200_OK)
def get_course_all_years(
    course_code: str,
    db: Session = Depends(get_db)
):
    courses = db.query(CourseModel).filter(CourseModel.course_code == course_code).order_by(CourseModel.catalog_year.desc()).all()

    if not courses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with code '{course_code}' not found"
        )

    return courses

# single course from specified year
@app.get("/courses/{course_code}/{catalog_year}", response_model=Course, status_code=status.HTTP_200_OK)
def get_single_course(
    course_code: str,
    catalog_year: str,
    db: Session = Depends(get_db)
):
    """Get a specific course from a specific catalog year."""
    course = db.query(CourseModel).filter(CourseModel.course_code == course_code).filter(CourseModel.catalog_year == catalog_year).first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course '{course_code}' not found for catalog year '{catalog_year}'"
        )

    return course

# return all possible prefixes 
@app.get("/prefixes", response_model=List[str], status_code=status.HTTP_200_OK)
def get_prefixes(
    db: Session = Depends(get_db)
):
    all_codes = db.query(CourseModel.course_code).distinct().all()

    prefixes = set()
    for code_tuple in all_codes:
        code = code_tuple[0]
        # Find where digits start
        prefix = ""
        for char in code:
            if char.isdigit():
                break
            prefix += char
        if prefix:
            prefixes.add(prefix.strip())

    return sorted(list(prefixes))

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok"}
