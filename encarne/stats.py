"""Show some statistics about encarne."""
import humanfriendly

from encarne.movie import Movie
from encarne.db import get_session


def show_stats(args):
    """Print how much has already been saved by reencoding."""
    session = get_session()
    Movie.clean_movies(session)
    movies = session.query(Movie).all()

    saved = 0
    failed = 0
    encoded = 0
    for movie in movies:
        saved += movie.original_size - movie.size
        if movie.failed:
            failed += 1
        elif movie.encoded:
            encoded += 1

    saved_formatted = humanfriendly.format_size(saved)
    print(f'Saved space: {saved_formatted}')
    print(f'Reencoded movies: {encoded}')
    print(f'Failed movies: {failed}')
