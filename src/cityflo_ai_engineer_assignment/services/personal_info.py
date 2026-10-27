"""Resume access rules, independent of MCP, logging, and databases."""

from copy import deepcopy
from typing import Any


class PersonalInfo:
    """Read the supplied resume without allowing callers to mutate its data."""

    def __init__(self, data: dict[str, Any]):
        self._data = deepcopy(data)

    def get_personal_info(self) -> dict[str, Any]:
        return {"personal_info": deepcopy(self._data["personal_info"])}

    def get_user_skills(self) -> dict[str, Any]:
        return {key: deepcopy(self._data[key]) for key in ("summary", "skills")}

    def get_work_experiance(self) -> dict[str, Any]:
        """Keep the public method spelling requested by the user."""
        return {"work_experience": deepcopy(self._data["work_experience"])}

    def get_personal_projects(self) -> dict[str, Any]:
        return {"projects": deepcopy(self._data["projects"])}

    def get_personal_achievements(self) -> dict[str, Any]:
        return {"education_and_achievements": deepcopy(self._data["education_and_achievements"])}

    def get_resume(self) -> dict[str, Any]:
        return deepcopy(self._data)

