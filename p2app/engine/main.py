# p2app/engine/main.py
#
# ICS 33 Spring 2025
# Project 2: Learning to Fly
#
# An object that represents the engine of the application.
#
# This is the outermost layer of the part of the program that you'll need to build,
# which means that YOU WILL DEFINITELY NEED TO MAKE CHANGES TO THIS FILE.

import sqlite3
from p2app.events import *


class Engine:
    """An object that represents the application's engine, whose main role is to
    process events sent to it by the user interface, then generate events that are
    sent back to the user interface in response, allowing the user interface to be
    unaware of any details of how the engine is implemented.
    """

    def __init__(self):
        """Initializes the engine"""
        self._connection = None


    def process_event(self, event):
        """A generator function that processes one event sent from the user interface,
        yielding zero or more events in response."""

        # This is a way to write a generator function that always yields zero values.
        # You'll want to remove this and replace it with your own code, once you start
        # writing your engine, but this at least allows the program to run.
        if isinstance(event, OpenDatabaseEvent):
            try:
                self._connection = sqlite3.connect(event.path())
                self._connection.execute('PRAGMA foreign_keys = ON;')
                yield DatabaseOpenedEvent(event.path())
            except Exception as e:
                yield DatabaseOpenFailedEvent(str(e))

        elif isinstance(event, CloseDatabaseEvent):
            if self._connection:
                self._connection.close()
                self._connection = None
            yield DatabaseClosedEvent()

        elif isinstance(event, QuitInitiatedEvent):
            if self._connection:
                self._connection.close()
                self._connection = None
            yield EndApplicationEvent()

        elif isinstance(event, StartContinentSearchEvent):
            yield from self.continent_search(event)

        elif isinstance(event, LoadContinentEvent):
            yield from self.continent_load(event)

        elif isinstance(event, SaveNewContinentEvent):
            yield from self.continent_new_save(event)

        elif isinstance(event, SaveContinentEvent):
            yield from self.continent_save_update(event)

        elif isinstance(event, StartCountrySearchEvent):
            yield from self.country_search(event)

        elif isinstance(event, LoadCountryEvent):
            yield from self.country_load(event)

        elif isinstance(event, SaveNewCountryEvent):
            yield from self.country_new_save(event)

        elif isinstance(event, SaveCountryEvent):
            yield from self.country_save_update(event)

        elif isinstance(event, StartRegionSearchEvent):
            yield from self.region_search(event)

        elif isinstance(event, LoadRegionEvent):
            yield from self.region_load(event)

        elif isinstance(event, SaveNewRegionEvent):
            yield from self.region_new_save(event)


    def continent_search(self, event):
        query = '''SELECT * FROM continent '''
        name = event.name()

        con_code = event.continent_code()
        parameters = None
        if name and con_code:
            query += '''WHERE continent_code = ?
                        AND name = ?;'''
            parameters = (con_code, name)

        elif name:
            query += '''WHERE name = ?;'''
            parameters = (name,)

        elif con_code:
            query += '''WHERE continent_code = ?;'''
            parameters = (con_code,)

        cursor = self._connection.execute(query, parameters)
        final = cursor.fetchall()

        for con in final:
            yield ContinentSearchResultEvent(Continent(*con))

    def continent_load(self, event):
        cursor = self._connection.execute('''SELECT * FROM continent
                                             WHERE continent_id = ?;''', (event.continent_id(),))

        continent_data = cursor.fetchone()

        if continent_data:
            yield ContinentLoadedEvent(Continent(*continent_data))
        else:
            yield ErrorEvent('Invalid ID')

    def continent_new_save(self, event):
        con = event.continent()
        con_code = con.continent_code
        con_name = con.name
        try:
            cursor = self._connection.execute('''INSERT INTO continent (continent_code, name)
                                                 VALUES (?, ?);''', (con_code, con_name))
            self._connection.commit()

            yield ContinentSavedEvent(con)
        except Exception:
            yield SaveContinentFailedEvent("Couldn't save continent")

    def continent_save_update(self, event):
        con = event.continent()
        con_code = con.continent_code
        con_name = con.name
        con_id = con.continent_id
        try:
            cursor = self._connection.execute('''UPDATE continent
                                                 SET continent_code = ?, name = ?
                                                 WHERE continent_id =?;''', (con_code, con_name, con_id))
            self._connection.commit()

            yield ContinentSavedEvent(con)
        except Exception:
            yield SaveContinentFailedEvent("Couldn't modify continent")

    def country_search(self, event):
        query = '''SELECT * FROM country '''
        name = event.name()
        coun_code = event.country_code()
        parameters = None

        if name and coun_code:
            query += '''WHERE country_code = ?
                        AND name = ?;'''
            parameters = (coun_code, name)

        elif name:
            query += '''WHERE name = ?;'''
            parameters = (name,)

        elif coun_code:
            query += '''WHERE country_code = ?;'''
            parameters = (coun_code,)

        cursor = self._connection.execute(query, parameters)
        final = cursor.fetchall()

        for country in final:
            yield CountrySearchResultEvent(Country(*country))

    def country_load(self, event):
        cursor = self._connection.execute('''SELECT * FROM country
                                             WHERE country_id = ?;''', (event.country_id(),))

        country_data = cursor.fetchone()

        if country_data:
            yield CountryLoadedEvent(Country(*country_data))
        else:
            yield ErrorEvent('Invalid ID')

    def country_new_save(self, event):
        coun = event.country()
        coun_code = coun.country_code
        coun_name = coun.name
        con_id = coun.continent_id
        coun_wiki = coun.wikipedia_link
        coun_keys = coun.keywords
        try:
            cursor = (self._connection.execute('''INSERT INTO country (country_code, name, 
                                                                       continent_id, wikipedia_link, keywords)
                                                  VALUES (?, ?, ?, ?, ?);''', (coun_code, coun_name,
                                                                               con_id, coun_wiki, coun_keys)))
            self._connection.commit()

            yield CountrySavedEvent(coun)
        except Exception:
            yield SaveCountryFailedEvent("Couldn't save country")

    def country_save_update(self, event):
        coun = event.country()
        coun_id = coun.country_id
        coun_code = coun.country_code
        coun_name = coun.name
        con_id = coun.continent_id
        coun_wiki = coun.wikipedia_link
        coun_keys = coun.keywords

        try:
            cursor = (self._connection.execute('''UPDATE country
                                                  SET country_code = ?, name = ?, 
                                                      continent_id = ?, wikipedia_link = ?, keywords = ?
                                                  WHERE country_id = ?;''', (coun_code, coun_name,
                                                                             con_id, coun_wiki, coun_keys, coun_id)))
            self._connection.commit()

            yield CountrySavedEvent(coun)
        except Exception:
            yield SaveCountryFailedEvent("Couldn't modify country")

    def region_search(self, event):
        query = '''SELECT * FROM region '''
        name = event.name()
        local_code = event.local_code()
        reg_code = event.region_code()
        parameters = None

        if name and local_code and reg_code:
            query += '''WHERE region_code = ?
                        AND local_code = ?
                        AND name = ?;'''
            parameters = (reg_code, local_code, name)

        elif name and local_code:
            query += '''WHERE local_code = ?
                        AND name = ?;'''
            parameters = (local_code, name)

        elif name and reg_code:
            query += '''WHERE region_code = ?
                        AND name = ?;'''
            parameters = (reg_code, name)

        elif local_code and reg_code:
            query += '''WHERE region_code = ?
                        AND local_code = ?;'''
            parameters = (reg_code, local_code)

        elif name:
            query += '''WHERE name = ?;'''
            parameters = (name,)

        elif local_code:
            query += '''WHERE local_code = ?;'''
            parameters = (local_code,)

        elif reg_code:
            query += '''WHERE region_code = ?;'''
            parameters = (reg_code,)

        cursor = self._connection.execute(query, parameters)
        final = cursor.fetchall()

        for region in final:
            yield RegionSearchResultEvent(Region(*region))

    def region_load(self, event):
        cursor = self._connection.execute('''SELECT * FROM region
                                             WHERE region_id = ?;''', (event.region_id(),))

        region_data = cursor.fetchone()

        if region_data:
            yield RegionLoadedEvent(Region(*region_data))
        else:
            yield ErrorEvent('Invalid ID')

    def region_new_save(self, event):
        reg = event.region()
        reg_code = reg.region_code
        loc_code = reg.local_code
        reg_name = reg.name
        con_id = reg.continent_id
        coun_id = reg.country_id
        reg_wiki = reg.wikipedia_link
        reg_keys = reg.keywords
        try:
            cursor = (self._connection.execute('''INSERT INTO region (region_code, local_code, name,
                                                                      continent_id, country_id,
                                                                      wikipedia_link, keywords)
                                                  VALUES (?, ?, ?, ?, ?, ?, ?);''', (reg_code, loc_code, reg_name,
                                                                                     con_id, coun_id,
                                                                                     reg_wiki, reg_keys)))
            self._connection.commit()

            yield RegionSavedEvent(reg)
        except Exception:
            yield SaveRegionFailedEvent("Couldn't save region")




