from csv import DictReader
from datetime import datetime
from json import loads
from pathlib import Path
from sys import argv

from jinja2 import Environment, FileSystemLoader, StrictUndefined


class Config:
    def __init__(self, file: Path):
        self._file = file
        self._validate_file()
        raw_config = loads(Path(argv[1]).read_text('utf-8'))

        self.work_dir = Path(raw_config.get("work_dir"))
        self.csv = self.work_dir / raw_config.get("csv")
        self.template = self.work_dir / raw_config.get("template")
        self.filename: str = raw_config.get("filename")
        self.output_dir = self._build_dir()
        self._validate_config()

    def _validate_file(self):
        if not self._file.is_file():
            raise FileNotFoundError("Provide path to config as script arguement")

    def _validate_config(self):
        if not all([self.csv, self.template, self.work_dir]):
            raise FileNotFoundError(f"values for 'template', 'csv', 'work_dir' must present in config")

    def _build_dir(self):
        dir_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dir_path = self.work_dir / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path


class Context:
    def __init__(self, csv_row: dict, idx: int, config: Config):
        self.data = csv_row
        self.idx = idx + 1
        self.config = config

    def output_file(self):
        if self.config.filename:
            try:
                return self.config.output_dir / self.config.filename.format(**self.data)
            except KeyError:
                raise RuntimeError("filename pattern in config is incorrect")
        return self.config.output_dir / f"result_{self.idx}.txt"


class FilesBuilder:
    def __init__(self, config_path: Path):
        self.config = Config(config_path)
        self.j2_env = Environment(
            loader=FileSystemLoader(self.config.work_dir),
            undefined=StrictUndefined
        )
        self.template = self.j2_env.get_template(self.config.template.name)

    def call(self):
        with self.config.csv.open(newline='') as csvfile:
            reader = DictReader(csvfile)
            for i, row in enumerate(reader):
                self._build_file(row, i)

    def _build_file(self, row, idx):
        context = Context(row, idx, self.config)
        output = self.template.render(**context.data)
        with context.output_file().open('w', encoding='utf-8') as f:
            f.write(output)


def main():
    if len(argv) < 2:
        raise FileNotFoundError("Provide path to config as script arguement")
    runner = FilesBuilder(Path(argv[1]))
    runner.call()


if __name__ == '__main__':
    main()
