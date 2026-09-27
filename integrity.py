import hashlib


CHUNK_SIZE = 4096


def create_hasher():
    return hashlib.sha256()


def update_hash(hasher, chunk):
    hasher.update(chunk)


def get_digest(hasher):
    return hasher.hexdigest()


def hash_file(file_path, chunk_size=CHUNK_SIZE):

    hasher = create_hasher()

    with open(file_path, "rb") as f:

        while chunk := f.read(chunk_size):

            update_hash(
                hasher,
                chunk
            )

    return get_digest(hasher)