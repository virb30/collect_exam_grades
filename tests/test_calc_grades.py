

from exam_grades import ENEMScrap


def test_calc_grade_average():
    expected = 16
    grades = [521.1, 542.4, 575.7, 552.4]

    assert ENEMScrap.calculate_grade_average(grades) == expected


def test_calc_essay_grade():
    expected = 9
    grade = 860.0

    assert ENEMScrap.calculate_essay_grade(grade) == expected
