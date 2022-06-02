from django.db.migrations import Migration


class ExtendableMigration:
    """
    Класс, который обходит все элементы списка операций миграции
    и на ходу добавляет новые операции.
    """

    def __init__(self, migration: Migration, backward: bool = False, **kwargs):
        self.migration = migration
        self.backward = backward
        self.iter_index = 0
        self.insert_index = 0
        self.kwargs = kwargs

    def iterate(self):
        while True:
            try:
                op = self.migration.operations[self.iter_index]
            except LookupError:
                break

            self.insert_index = self.iter_index
            self.process(op, **self.kwargs)
            self.iter_index += 1

    def process(self, operation, **kwargs):
        raise NotImplementedError

    def insert_before(self, operation):
        # Добавление операции перед текущей.
        if self.backward:
            self.insert_index += 1
            self.migration.operations.insert(
                self.insert_index,
                operation
            )
            self.iter_index += 1
        else:
            self.migration.operations.insert(
                self.insert_index,
                operation
            )
            self.iter_index += 1

    def insert_after(self, operation):
        # Добавление операции после текущей.
        if self.backward:
            self.migration.operations.insert(
                self.insert_index,
                operation
            )
            self.iter_index += 1
        else:
            self.insert_index += 1
            self.migration.operations.insert(
                self.insert_index,
                operation
            )
            self.iter_index += 1
