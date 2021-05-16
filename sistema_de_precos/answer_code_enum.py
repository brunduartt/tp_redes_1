from enum import Enum


class AnswerCode(Enum):
    NOT_FOUND = 404
    BAD_REQUEST = 400
    OK = 200
    ACCEPTED = 202
    CREATED = 201
