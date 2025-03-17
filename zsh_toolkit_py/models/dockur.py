from typing import Union, List

from docker import DockerClient, APIClient
from docker.models.containers import Container
from docker.models.images import Image, RegistryData

DockerConnection = Union[DockerClient, APIClient]


def _get_clean_image_name(full: str):
    if ':' in full:
        return full[0:full.index(':')]
    else:
        return full


def _get_image_digest_hash(data: Union[Image, RegistryData]) -> str:
    if isinstance(data, Image):
        digest = data.attrs.get("RepoDigests")

        if digest:
            return digest[0].split('@')[1]
        else:
            ''
    else:
        return data.attrs['Descriptor']['digest']


def _get_latest_image_hash(conn: DockerConnection, image_tag: str) -> str:
    data = conn.images.get_registry_data(image_tag)

    return _get_image_digest_hash(data) if data else ''


class ContainerMeta:

    def __init__(self, conn: DockerConnection, name: str, image: str):
        self._conn = conn
        self.name: str = name
        self.image_tag: str = image
        self.image_tag_clean: str = _get_clean_image_name(image)
        self.latest_hash: Union[str, None] = None
        self.container: Union[Container, None] = None
        self.update_container_stats()

    def update_container_stats(self) -> None:
        res = self._conn.containers.list(filters={'name': f'^/{self.name}$'}, all=True)

        if res:
            if len(res) > 1:
                raise Exception(f'Container name not unique. How the fuck did that happen: {self.name}')
            self.container = res[0]
        else:
            self.container = None

        self.latest_hash = _get_latest_image_hash(self._conn, self.image_tag)

    @property
    def current_hash(self) -> str:
        # return self.container.image.id if self.container else ''
        return _get_image_digest_hash(self.container.image) if self.container else ''

    @property
    def image(self) -> Union[Image, None]:
        return self.container.image if self.container else None

    @property
    def image_tags(self) -> List[str]:
        return self.image.tags if self.container else []

    @property
    def update_available(self):
        return self.current_hash != self.latest_hash

    def stats_str(self) -> str:
        if self.container:
            if len(self.image_tags) > 1:
                tags = '[{}]'.format(', '.join(self.image_tags))
            else:
                tags = self.image_tags[0]
            return f'{str.ljust(self.container.status, 7)} :: {tags} :: {self.container.image.id}'

        return ''

    def __str__(self):
        if self.current_hash:
            status = 'Update available' if self.update_available else 'Up to date'
        elif self.latest_hash:
            status = f'Latest: {self.latest_hash}'
        else:
            status = 'No Data'

        return f'{self.name} :: {self.image_tag} :: {status}'
