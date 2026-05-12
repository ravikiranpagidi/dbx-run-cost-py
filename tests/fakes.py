from __future__ import annotations


class FakeDataFrame:
    def __init__(self, rows):
        self.rows = rows
        self.write = FakeWriter(self)

    def collect(self):
        return self.rows


class FakeWriter:
    def __init__(self, df):
        self.df = df
        self.format_name = None
        self.mode_name = None
        self.options = {}
        self.saved_table = None
        self.saved_path = None

    def format(self, name):
        self.format_name = name
        return self

    def mode(self, name):
        self.mode_name = name
        return self

    def option(self, key, value):
        self.options[key] = value
        return self

    def saveAsTable(self, table):
        self.saved_table = table

    def save(self, path):
        self.saved_path = path


class FakeSpark:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.queries = []
        self.created = []

    def sql(self, query):
        self.queries.append(query)
        return FakeDataFrame(self.rows)

    def createDataFrame(self, rows):
        df = FakeDataFrame(rows)
        self.created.append(df)
        return df
