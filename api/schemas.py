from pydantic import BaseModel, ConfigDict
from typing import Optional, Union, List

# catalog_year seperated by _ not -
class Course(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course_code: str
    course_name: str
    credits: Optional[Union[int, List[int]]] = None
    course_description: Optional[str] = None
    prereqs: Optional[List[str]] = None
    coreqs: Optional[List[str]] = None
    class_levels: Optional[List[str]] = None
    repeats_allowed_for_credit: Optional[int] = None
    catalog_year: str

class CourseFilter(BaseModel):
    course_code: Optional[str] = None
    course_prefix: Optional[str] = None
    catalog_year: Optional[str] = None

    # Prereq & Coreq based
    has_prereqs: Optional[bool] = None
    has_coreqs: Optional[bool] = None
    prereq_contains: Optional[str] = None
    coreq_contains: Optional[str] = None

    # Class level
    class_level: Optional[str] = None

    # Repeatability
    repeats_allowed: Optional[bool] = None
    min_repeat: Optional[int] = None

    # Sorting
    sort_by: Optional[str] = "course_code" 