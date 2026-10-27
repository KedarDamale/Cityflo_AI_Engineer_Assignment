"""Load the packaged resume once per server lifespan."""

import json
from importlib.resources import files

from ..services.personal_info import PersonalInfo


class PersonalInfoFactory:
    @staticmethod
    def create() -> PersonalInfo:
        folder = files("cityflo_ai_engineer_assignment").joinpath("my_resume")
        return PersonalInfo(
            json.loads(folder.joinpath("personal_info.json").read_text(encoding="utf-8")),
        )
