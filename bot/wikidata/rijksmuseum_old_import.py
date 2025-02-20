#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
C:\pywikibot\core>add_category.py -lang:wikidata -family:wikidata -file:categories_not_category.txt -namespace:0


"""
import json
import pywikibot
from pywikibot import pagegenerators
import urllib
import re
import pywikibot.data.wikidataquery as wdquery
import datetime

class PaintingsBot:
    """
    A bot to enrich and create monuments on Wikidata
    """
    def __init__(self, dictGenerator, paintingIdProperty):
        """
        Arguments:
            * generator    - A generator that yields Dict objects.

        """
        self.generator = dictGenerator
        self.repo = pywikibot.Site().data_repository()
        
        self.paintingIdProperty = paintingIdProperty
        self.paintingIds = self.fillCache(self.paintingIdProperty)
        
    def fillCache(self, propertyId, queryoverride=u'', cacheMaxAge=0):
        '''
        Query Wikidata to fill the cache of monuments we already have an object for
        '''
        result = {}
        if queryoverride:
            query = queryoverride
        else:
            query = u'CLAIM[195:190804] AND CLAIM[%s]' % (propertyId,)
        wd_queryset = wdquery.QuerySet(query)

        wd_query = wdquery.WikidataQuery(cacheMaxAge=cacheMaxAge)
        data = wd_query.query(wd_queryset, props=[str(propertyId),])

        if data.get('status').get('error')=='OK':
            expectedItems = data.get('status').get('items')
            props = data.get('props').get(str(propertyId))
            for prop in props:
                # FIXME: This will overwrite id's that are used more than once.
                # Use with care and clean up your dataset first
                result[prop[2]] = prop[0]

            if expectedItems==len(result):
                pywikibot.output('I now have %s items in cache' % expectedItems)

        return result
                        
    def run(self):
        """
        Starts the robot.
        """
        rijksmuseum = pywikibot.ItemPage(self.repo, u'Q190804')
        for painting in self.generator:
            # Buh, for this one I know for sure it's in there
            
            
            paintingId = painting['artObject']['objectNumber']
            uri = u'https://www.rijksmuseum.nl/nl/collectie/%s' % (paintingId,)
            #europeanaUrl = u'http://europeana.eu/portal/record/%s.html' % (painting['object']['about'],)

            print paintingId
            print uri

            dcCreatorName = painting['artObject']['principalOrFirstMaker'].strip()


            #dcCreatorName = u''

            #for agent in painting['object']['agents']:
            #    if agent.get('about')== dcCreator:
            #        #print u'Found my agent'
            #        if u',' in agent['prefLabel']['def'][0]:
            #            (surname, givenname) = agent['prefLabel']['def'][0].split(u',')
            #            dcCreatorName = u'%s %s' % (givenname.strip(), surname.strip(),)
            #        else:
            #            dcCreatorName = agent['prefLabel']['def'][0]
            
            #print painting['object']['language']
            #print painting['object']['title']
            #print painting['object']['about']
            #print painting['object']['proxies'][0]['dcCreator']['def'][0]
            #print painting['object']['proxies'][0]['dcFormat']['def'][0]
            #print painting['object']['proxies'][0]['dcIdentifier']['def'][0]
            #print painting['object']['proxies'][0]['dcIdentifier']['def'][1]
            
            paintingItem = None
            newclaims = []
            if paintingId in self.paintingIds:
                paintingItemTitle = u'Q%s' % (self.paintingIds.get(paintingId),)
                print paintingItemTitle
                paintingItem = pywikibot.ItemPage(self.repo, title=paintingItemTitle)

            else:
                
                #print 'bla'
                #monumentItem = pywikibot.ItemPage(self.repo, title=u'')

                
                        #print dcCreatorName


                data = {'labels': {},
                        'descriptions': {},
                        }

                data['labels']['nl'] = {'language': 'nl', 'value': painting['artObject']['title']}
                

                if dcCreatorName:
                    data['descriptions']['en'] = {'language': u'en', 'value' : u'painting by %s' % (dcCreatorName,)}
                    data['descriptions']['nl'] = {'language': u'nl', 'value' : u'schilderij van %s' % (dcCreatorName,)}
                    

                print data
                
                identification = {}
                summary = u'Creating new item with data from %s ' % (uri,)
                pywikibot.output(summary)
                #monumentItem.editEntity(data, summary=summary)
                result = self.repo.editEntity(identification, data, summary=summary)
                #print result
                paintingItemTitle = result.get(u'entity').get('id')
                paintingItem = pywikibot.ItemPage(self.repo, title=paintingItemTitle)

                newclaim = pywikibot.Claim(self.repo, u'P%s' % (self.paintingIdProperty,))
                newclaim.setTarget(paintingId)
                pywikibot.output('Adding new id claim to %s' % paintingItem)
                paintingItem.addClaim(newclaim)

                self.addReference(paintingItem, newclaim, uri)
                
                newqualifier = pywikibot.Claim(self.repo, u'P195') #Add collection, isQualifier=True
                newqualifier.setTarget(rijksmuseum)
                pywikibot.output('Adding new qualifier claim to %s' % paintingItem)
                newclaim.addQualifier(newqualifier)

                collectionclaim = pywikibot.Claim(self.repo, u'P195')
                collectionclaim.setTarget(rijksmuseum)
                pywikibot.output('Adding collection claim to %s' % paintingItem)
                paintingItem.addClaim(collectionclaim)

                self.addReference(paintingItem, collectionclaim, uri)

                
            
            if paintingItem and paintingItem.exists():
                
                data = paintingItem.get()
                claims = data.get('claims')
                #print claims

                # located in
                if u'P276' not in claims:
                    newclaim = pywikibot.Claim(self.repo, u'P276')
                    newclaim.setTarget(rijksmuseum)
                    pywikibot.output('Adding located in claim to %s' % paintingItem)
                    paintingItem.addClaim(newclaim)

                    self.addReference(paintingItem, newclaim, uri)
                    

                # instance of always painting while working on the painting collection
                if u'P31' not in claims:
                    
                    dcformatItem = pywikibot.ItemPage(self.repo, title='Q3305213')

                    newclaim = pywikibot.Claim(self.repo, u'P31')
                    newclaim.setTarget(dcformatItem)
                    pywikibot.output('Adding instance claim to %s' % paintingItem)
                    paintingItem.addClaim(newclaim)

                    self.addReference(paintingItem, newclaim, uri)


                # creator        
                if u'P170' not in claims and dcCreatorName:
                    creategen = pagegenerators.PreloadingEntityGenerator(pagegenerators.WikidataItemGenerator(pagegenerators.SearchPageGenerator(dcCreatorName, step=None, total=10, namespaces=[0], site=self.repo)))
                    
                    newcreator = None


                    for creatoritem in creategen:
                        print creatoritem.title()
                        if creatoritem.get().get('labels').get('en') == dcCreatorName or creatoritem.get().get('labels').get('nl') == dcCreatorName:
                            print creatoritem.get().get('labels').get('en')
                            print creatoritem.get().get('labels').get('nl')
                            # Check occupation and country of citizinship
                            if u'P106' in creatoritem.get().get('claims') and (u'P21' in creatoritem.get().get('claims') or u'P800' in creatoritem.get().get('claims')):
                                newcreator = creatoritem
                                continue
                        elif (creatoritem.get().get('aliases').get('en') and dcCreatorName in creatoritem.get().get('aliases').get('en')) or (creatoritem.get().get('aliases').get('nl') and dcCreatorName in creatoritem.get().get('aliases').get('nl')):
                            if u'P106' in creatoritem.get().get('claims') and (u'P21' in creatoritem.get().get('claims') or u'P800' in creatoritem.get().get('claims')):
                                newcreator = creatoritem
                                continue

                    if newcreator:
                        pywikibot.output(newcreator.title())

                        newclaim = pywikibot.Claim(self.repo, u'P170')
                        newclaim.setTarget(newcreator)
                        pywikibot.output('Adding creator claim to %s' % paintingItem)
                        paintingItem.addClaim(newclaim)

                        self.addReference(paintingItem, newclaim, uri)

                        print creatoritem.title()
                        print creatoritem.get()
                            
                            

                        

                    else:
                        pywikibot.output('No item found for %s' % (dcCreatorName, ))
                else:
                    print u'Already has a creator'

                """
                # date of creation
                if u'P571' not in claims:
                    if painting['object']['proxies'][0].get('dctermsCreated'):
                        dccreated = painting['object']['proxies'][0]['dctermsCreated']['def'][0].strip()
                        if len(dccreated)==4: # It's a year
                            newdate = pywikibot.WbTime(year=dccreated)
                            newclaim = pywikibot.Claim(self.repo, u'P571')
                            newclaim.setTarget(newdate)
                            pywikibot.output('Adding date of creation claim to %s' % paintingItem)
                            paintingItem.addClaim(newclaim)

                            self.addReference(paintingItem, newclaim, uri)


                # material used
                if u'P186' not in claims:
                    dcFormats = { u'http://vocab.getty.edu/aat/300014078' : u'Q4259259', # Canvas
                                  u'http://vocab.getty.edu/aat/300015050' : u'Q296955', # Oil paint
                                  }
                    if painting['object']['proxies'][0].get('dcFormat') and painting['object']['proxies'][0]['dcFormat'].get('def'):
                        for dcFormat in painting['object']['proxies'][0]['dcFormat']['def']:
                            if dcFormat in dcFormats:
                                dcformatItem = pywikibot.ItemPage(self.repo, title=dcFormats[dcFormat])

                                newclaim = pywikibot.Claim(self.repo, u'P186')
                                newclaim.setTarget(dcformatItem)
                                pywikibot.output('Adding material used claim to %s' % paintingItem)
                                paintingItem.addClaim(newclaim)

                                self.addReference(paintingItem, newclaim, uri)
                """
                ## Handle 
                #if u'P1184' not in claims:
                #    handleUrl = painting['object']['proxies'][0]['dcIdentifier']['def'][0]
                #    handle = handleUrl.replace(u'http://hdl.handle.net/', u'')
                #    
                #    newclaim = pywikibot.Claim(self.repo, u'P1184')
                #    newclaim.setTarget(handle)
                #    pywikibot.output('Adding handle claim to %s' % paintingItem)
                #    paintingItem.addClaim(newclaim
                #    self.addReference(paintingItem, newclaim, uri)

                # Europeana ID
                #if u'P727' not in claims:
                #    europeanaID = painting['object']['about'].lstrip('/')
                #    newclaim = pywikibot.Claim(self.repo, u'P727')
                #    newclaim.setTarget(europeanaID)
                #    pywikibot.output('Adding Europeana ID claim to %s' % paintingItem)
                #    paintingItem.addClaim(newclaim)
                #    self.addReference(paintingItem, newclaim, uri)

    def addReference(self, paintingItem, newclaim, uri):
        """
        Add a reference with a retrieval url and todays date
        """
        pywikibot.output('Adding new reference claim to %s' % paintingItem)
        refurl = pywikibot.Claim(self.repo, u'P854') # Add url, isReference=True
        refurl.setTarget(uri)
        refdate = pywikibot.Claim(self.repo, u'P813')
        today = datetime.datetime.today()
        date = pywikibot.WbTime(year=today.year, month=today.month, day=today.day)
        refdate.setTarget(date)
        newclaim.addSources([refurl, refdate])

def getPaintingGenerator(query=u''):
    '''
    Bla %02d
    ''' 
    #url = 'http://europeana.eu/api/v2/record/92034/GVNRC_MAU01_%04d.json?wskey=1hfhGH67Jhs&profile=full'
    #url = 'http://europeana.eu/api/v2/record/90402/SK_C_%d.json?wskey=1hfhGH67Jhs&profile=full'
    #url = 'http://europeana.eu/api/v2/record/90402/SK_A_%d.json?wskey=1hfhGH67Jhs&profile=full'
    url = 'https://www.rijksmuseum.nl/api/nl/collection/SK-A-%d?key=NJwVKOnk&format=json'

    for i in range(3445, 3447):
        
        apiPage = urllib.urlopen(url % (i,))
        apiData = apiPage.read()
        jsonData = json.loads(apiData)
        if jsonData.get('artObject'):
            yield jsonData
        else:
            print jsonData

        




def main():
    paintingGen = getPaintingGenerator()
    



    paintingsBot = PaintingsBot(paintingGen, 217)
    paintingsBot.run()
    
    

if __name__ == "__main__":
    main()
