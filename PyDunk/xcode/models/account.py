
class Account:
    __slots__ = ('_data', 'email', 'status', 'lfirst', 'llast', 'first', 'last', 'developer_id', 'person_id',)

    def __init__(
        self,
        email: str,
        status: str,
        lfirst: str,
        llast: str,
        first: str,
        last: str,
        developer_id: str,
        person_id: int,
    ):
        self.email = email
        self.status = status
        self.lfirst = lfirst
        self.llast = llast
        self.first = first
        self.last = last
        self.developer_id = developer_id
        self.person_id = person_id

    def __repr__(self):
        return f"{self.__class__.__name__}({self.email!r}, {self.status!r}, {self.person_id!r}, {self.first!r}, {self.last!r})"

    @property
    def name(self):
        return f"{self.first} {self.last}"

    @classmethod
    def from_api(cls, data: dict):
        c = cls(
            data['email'],
            data['developerStatus'],
            data['firstName'],
            data['lastName'],
            data['dsFirstName'] if isinstance(data['dsFirstName'], str) else data['firstName'],
            data['dsLastName'] if isinstance(data['dsLastName'], str) else data['lastName'],
            data['developerId'],
            data['personId'],
        )
        c._data = data
        return c

