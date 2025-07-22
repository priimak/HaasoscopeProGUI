class ValueContainer[T]:
    def __init__(self, value: T | None):
        self.__value = value

    @property
    def value(self) -> T | None:
        return self.__value

    @value.setter
    def value(self, value: T | None):
        self.__value = value

    def __call__(self) -> T | None:
        return self.__value
