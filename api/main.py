from fastapi import FastAPI, status, HTTPException, Depends
from schemas import Course, CourseFilter
from typing import List
from database import get_db
from sqlalchemy.orm import Session


app = FastAPI()

"""
Status codes to use for GET:
    status.HTTP_200_OK
    status.HTTP_404_NOT_FOUND 

for failures:
    raise HTTPEsception(status_code= , detail= "")
"""

@app.get("/courses", response_model=List[Course], status_code=status.HTTP_200_OK)
def get_courses(
    filters: CourseFilter = Depends(),
    db: Session = Depends(get_db)
):
    pass

@app.get("/courses/{course_code}", response_model=Course, status_code=status.HTTP_200_OK)
def get_single_course(
    course_code: str,
    db: Session = Depends(get_db)
):
    pass

@app.get("/catalog_years", response_model=List[str], status_code=status.HTTP_200_OK)
def get_catalog_years(
    db: Session = Depends(get_db)
):
    pass

@app.get("/departments", response_model=List[str], status_code=status.HTTP_200_OK)
def get_prefixes(
    db: Session = Depends(get_db)
):
    pass

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok"}