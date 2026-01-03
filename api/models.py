from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
import json
from typing import Optional, Union, List


Base = declarative_base()

class CourseModel(Base):
    __tablename__ = "courses"

    course_code = Column(String, primary_key=True)
    catalog_year = Column(String, primary_key=True)
    
    course_name = Column(Text)
    _credits = Column("credits", Text)
    course_description = Column(Text)
    _prereqs = Column("prereqs", Text)
    _coreqs = Column("coreqs", Text)
    _class_levels = Column("class_levels", Text)
    repeats_allowed_for_credit = Column(Integer)

    @hybrid_property
    def credits(self) -> Optional[Union[int, List[int]]]:
        """Examples: '[1, 4]' or '3' """
        if self._credits is None:
            return None
        try:
            return json.loads(self._credits)
        except(json.JSONDecodeError, TypeError):
            try:
                return int(self._credits)
            except ValueError:
                return None

    @hybrid_property
    def prereqs(self) -> Optional[List[str]]:
        """Parse prereqs from JSON string to list"""
        if not self._prereqs or self._prereqs == '':
            return None
        try:
            return json.loads(self._prereqs)
        except:
            return None

    @hybrid_property
    def coreqs(self) -> Optional[List[str]]:
        """Parse coreqs from JSON string to list"""
        if not self._coreqs or self._coreqs == '':
            return None
        try:
            return json.loads(self._coreqs)
        except:
            return None

    @hybrid_property
    def class_levels(self) -> Optional[List[str]]:
        """Parse class_levels from JSON string to list"""
        if not self._class_levels or self._class_levels == '':
            return None
        try:
            return json.loads(self._class_levels)
        except:
            return None