

from io import BytesIO, TextIOWrapper
from exam_grades import ENEMScrap


def test_read_file_lines():

    file = BytesIO(b'00001;John Doe;123.456.789-01;2019\n')
    expected = [b'00001;John Doe;123.456.789-01;2019']

    assert ENEMScrap.read_file_lines(file) == expected


def test_read_file_lines_empty():
    file = BytesIO(b'')
    expected = []

    assert ENEMScrap.read_file_lines(file) == expected


def test_read_file_lines_multilines():
    file = BytesIO(
        b'''00001;John Doe;123.456.789-01;2019\n00002;Jane Doe;123.456.789-02;2019\n''')

    expected = [b'00001;John Doe;123.456.789-01;2019',
                b'00002;Jane Doe;123.456.789-02;2019']

    lines = ENEMScrap.read_file_lines(file)

    assert lines == expected
    assert len(lines) == 2
