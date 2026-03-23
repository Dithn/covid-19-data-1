import re
import pandas as pd


class NumericCleaner:
    numeric_words: dict = {
        "million": {
            "words": [
                "million",
                "millió",
                "millón",
                "millones",
                "millions",
                "millionen",
                "milioni",
                "milione",
                "miljoen",
                "milhão",
                "milhões",
            ],
            "factor": 1e6,
        },
        "ten_thousand": {
            "words": ["万"],
            "factor": 1e4,
        },
        "thousand": {
            "words": ["thousand", "ezren", "mil", "duizend", "mila", "mille", "tausend"],
            "factor": 1e3,
        },
        "hundred": {"words": ["hundred", "cien", "cent", "hundert", "honderd", "cem", "cento"], "factor": 1e2},
        "one": {"words": [""], "factor": 1},
    }
    regex_number_verbose_template: str = "(?:(?P<{}>\d+(?:\.\d+)?)\s?(?:{}))?"
    regex_number_not_verbose: str = r"\d+((.\d+)+)?"
    regex_number_not_verbose_correct: str = r"\d+((.\d{3})+)?"

    @property
    def regex_number_verbose(self):
        regex = [
            self.regex_number_verbose_template.format(k, "|".join(v["words"])) for k, v in self.numeric_words.items()
        ]
        regex = "\s?".join(regex)
        return regex

    def _match_numeric_words(self, num_as_str):
        match = re.search(self.regex_number_verbose, num_as_str)
        numbers = match.groupdict(default=0)
        return numbers

    def _build_number(self, numbers):
        value = 0
        for k, v in numbers.items():
            value += float(v) * self.numeric_words[k]["factor"]
        return int(value)

    def _to_str(self, num_as_str):
        if not isinstance(num_as_str, str):
            return str(num_as_str)
        return num_as_str

    def _is_verbose(self, num):
        pattern = re.compile(self.regex_number_not_verbose)
        match = pattern.fullmatch(num)
        return not match

    def _is_not_verbose_and_incorrect(self, num):
        pattern = re.compile(self.regex_number_not_verbose_correct)
        match = pattern.fullmatch(num)
        return not match

    def clean_verbose_number(self, num_as_str):
        number_dict = self._match_numeric_words(num_as_str)
        # print(number_dict)
        number = self._build_number(number_dict)
        return number

    def run(self, num_as_str):
        num = self._to_str(num_as_str).strip()
        if self._is_verbose(num):
            num = self.clean_verbose_number(num)
        elif self._is_not_verbose_and_incorrect(num):
            raise ValueError("The format of the number seems to be not correct! Please review.")
        num = re.sub(r"[^0-9]", "", str(num))
        num = int(num)
        return num


def clean_count(count):
    cleaner = NumericCleaner()
    return cleaner.run(count)


def _series_to_int64(ds):
    return ds.astype(pd.Int64Dtype())


def _series_to_float(ds):
    return ds.astype(float)


def metrics_to_num_int(df, metrics):
    for metric in metrics:
        if metric in df.columns:  # and any(df[metric].isnull()):
            df.loc[:, metric] = _series_to_int64(df[metric])
    return df


def metrics_to_num_float(df, metrics):
    for metric in metrics:
        if metric in df.columns:  # and any(df[metric].isnull()):
            df.loc[:, metric] = _series_to_float(df[metric])
    return df
