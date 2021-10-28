from io import BytesIO, TextIOWrapper
from exam_grades import ENEMScrap
from pathlib import Path
from pytest_mock import MockerFixture


class TestReadFile:

    def test_read_file_lines(self, mocker: MockerFixture):
        content = BytesIO(b'00001;John Doe;123.456.789-01;2019\n')

        self._mock_pathlib(mocker, content)

        file = Path()

        expected = ['00001;John Doe;123.456.789-01;2019']

        assert ENEMScrap.read_file_lines(file) == expected

    def test_read_file_lines_empty(self, mocker: MockerFixture):
        content = BytesIO(b'')
        expected = []

        self._mock_pathlib(mocker, content)

        file = Path()

        assert ENEMScrap.read_file_lines(file) == expected

    def test_read_file_lines_multilines(self, mocker: MockerFixture):
        content = BytesIO(
            b'''00001;John Doe;123.456.789-01;2019\n00002;Jane Doe;123.456.789-02;2019\n''')

        expected = ['00001;John Doe;123.456.789-01;2019',
                    '00002;Jane Doe;123.456.789-02;2019']

        self._mock_pathlib(mocker, content)

        file = Path()

        lines = ENEMScrap.read_file_lines(file)

        assert lines == expected
        assert len(lines) == 2

    def _mock_pathlib(self, mocker: MockerFixture, content):
        # mock exists
        mocker.patch(
            'pathlib.Path.exists',
            return_value=True
        )

        # mock read
        mocker.patch(
            'pathlib.Path.open',
            return_value=TextIOWrapper(content)
        )
