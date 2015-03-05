import ConfigParser, logging
from pacman103.conf import log

def test_deepest_parent():
    assert(
        log.deepest_parent( [], 'pacman103.core.mapper.routing_algorithms.dijkstra_algorithm' ) ==
        None
    )
    assert(
        log.deepest_parent(
            ['pacman103.core.mapper.routing_algorithms'],
            'pacman103.core.mapper.routing_algorithms.dijkstra_algorithm'
        ) == 'pacman103.core.mapper.routing_algorithms'
    )
    assert(
        log.deepest_parent(
            ['pacman103.core.mapper.routing_algorithms','pacman103.core.dao'],
            'pacman103.core.mapper.routing_algorithms.dijkstra_algorithm'
        ) == 'pacman103.core.mapper.routing_algorithms'
    )
    assert(
        log.deepest_parent(
            ['pacman103.core.mapper.routing_algorithms','pacman103.core.dao','pacman103.core'],
            'pacman103.core.mapper.routing_algorithms.dijkstra_algorithm'
        ) == 'pacman103.core.mapper.routing_algorithms'
    )
    assert(
        log.deepest_parent(
            ['pacman103.core.dao','pacman103.core'],
            'pacman103.core.mapper.routing_algorithms.dijkstra_algorithm'
        ) == 'pacman103.core'
    )

def test_level_of_deepest_parent():
    assert(
        log.level_of_deepest_parent({}, 'pacman103.core.mapper.routing_algorithms.dijkstra_algorithm')
        is None
    )
    assert(
        log.level_of_deepest_parent(
            {
                'pacman103.core.mapper': logging.ERROR,
            },
            'pacman103.core.mapper.routing_algorithms.dijkstra_algorithm'
        )
        == logging.ERROR
    )
    assert(
        log.level_of_deepest_parent(
            {
                'pacman103.core.mapper': logging.ERROR,
                'pacman103.core.mapper.routing_algorithms': logging.CRITICAL,
            },
            'pacman103.core.mapper.routing_algorithms.dijkstra_algorithm'
        )
        == logging.CRITICAL
    )

def test_construct_logging_parents():
    config = ConfigParser.RawConfigParser()
    assert( log.construct_logging_parents( config ) == {} )

    config = ConfigParser.RawConfigParser()
    config.add_section( "Logging" )
    config.set( "Logging", "default", "debug" )
    config.set( "Logging", "debug", "abcd" )
    assert( log.construct_logging_parents( config ) ==
            {
                'abcd': logging.DEBUG,
            }
    )

    config = ConfigParser.RawConfigParser()
    config.add_section( "Logging" )
    config.set( "Logging", "default", "debug" )
    config.set( "Logging", "debug", "abcd, efgh" )
    assert( log.construct_logging_parents( config ) ==
            {
                'abcd': logging.DEBUG,
                'efgh': logging.DEBUG,
            }
    )

    config = ConfigParser.RawConfigParser()
    config.add_section( "Logging" )
    config.set( "Logging", "default", "debug" )
    config.set( "Logging", "debug", "a,  b   ")
    config.set( "Logging", "info",  "  c, d" )
    config.set( "Logging", "warning", "e,f,g" )
    config.set( "Logging", "error", "h.i, j.k" )
    config.set( "Logging", "critical", "l.m.n" )
    assert( log.construct_logging_parents( config ) ==
            {
                'a': logging.DEBUG, 'b': logging.DEBUG,
                'c': logging.INFO, 'd': logging.INFO,
                'e': logging.WARNING, 'f': logging.WARNING, 'g': logging.WARNING,
                'h.i': logging.ERROR, 'j.k': logging.ERROR,
                'l.m.n': logging.CRITICAL,
            }
    )

def test_configured_filter():
    config = ConfigParser.RawConfigParser()
    config.add_section( "Logging" )
    config.set( "Logging", "default", "debug" )
    config.set( "Logging", "debug", "a,  b   ")
    config.set( "Logging", "info",  "  c, d" )
    config.set( "Logging", "warning", "e,f,g" )
    config.set( "Logging", "error", "h.i, j.k" )
    config.set( "Logging", "critical", "l.m.n" )

    f = log.ConfiguredFilter( config )

    class FauxRecord( object ):
        def __init__( self, name, level ):
            self.name = name
            self.levelno = level

    for (p,l) in zip(
            [True, True, True, True, True],
            [logging.DEBUG, logging.INFO, logging.WARNING,
             logging.ERROR, logging.CRITICAL]
        ):
        for n in ['a', 'b', 'z.y.z']:
            assert( f.filter( FauxRecord( n, l ) ) == p )

    for (p,l) in zip(
            [False, True, True, True, True],
            [logging.DEBUG, logging.INFO, logging.WARNING,
             logging.ERROR, logging.CRITICAL]
        ):
        for n in ['c.f.g.h', 'd']:
            assert( f.filter( FauxRecord( n, l ) ) == p )

    for (p,l) in zip(
            [False, False, True, True, True],
            [logging.DEBUG, logging.INFO, logging.WARNING,
             logging.ERROR, logging.CRITICAL]
        ):
        for n in ['e.zzzz.yyyy', 'f', 'g']:
            assert( f.filter( FauxRecord( n, l ) ) == p )

    for (p,l) in zip(
            [False, False, False, True, True],
            [logging.DEBUG, logging.INFO, logging.WARNING,
             logging.ERROR, logging.CRITICAL]
        ):
        for n in ['h.i', 'j.k']:
            assert( f.filter( FauxRecord( n, l ) ) == p )

    for (p,l) in zip(
            [False, False, False, False, True],
            [logging.DEBUG, logging.INFO, logging.WARNING,
             logging.ERROR, logging.CRITICAL]
        ):
        for n in ['l.m.n']:
            assert( f.filter( FauxRecord( n, l ) ) == p )
