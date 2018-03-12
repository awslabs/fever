import multiprocessing
from subprocess import run, PIPE
import os

from persistence.local_persistence import LocalQueuePersistence


#Load Java classpath for stanford corenlp using gradle. this will also install it if missing
if 'CLASSPATH' not in os.environ:
    print("no cp")
    if not (os.path.exists('build') and os.path.exists('build/classpath.txt')):
        print("no bld")
        print("Generating classpath")
        r=run(["./gradlew", "writeClasspath"],stdout=PIPE, stderr=PIPE, universal_newlines=True)
        print(r.stdout)
        print(r.stderr)

    print("Loading classpath")
    os.environ['CLASSPATH'] = open('build/classpath.txt','r').read()
    print("Done")


from dataset.reader.wiki_parser import WikiParser

print("ccp")


article = "Mexico"
doc = """
{{about|the country in North America}}
{{pp-semi-indef}}
{{pp-move-indef}}
{{Use mdy dates|date=August 2017}}
{{Coord|23|N|102|W|display=title}}{{Use American English|date=August 2016}}
{{Infobox country
|conventional_long_name = United Mexican States
|common_name = Mexico
|native_name = {{native name|es|Estados Unidos Mexicanos}}
|image_flag = Flag of Mexico.svg
|alt_flag =File:Mexican States Standard.svg
|image_coat = Coat of arms of Mexico.svg
|alt_coat =File:Seal of the Government of Mexico (linear).svg
|symbol_type = Coat of arms
|national_motto =
|national_anthem = ''[[Himno Nacional Mexicano]]''<br/>{{small|({{lang-en|"Mexican National Anthem"}})}}<br/><br/><center>[[File:Himno Nacional Mexicano instrumental.ogg]]</center>
|image_map = MEX orthographic.svg
|map_width = 220px
|capital = [[Mexico City]]
|coordinates = {{Coord|19|26|N|99|08|W|type:city}}
|largest_city = Mexico City
|official_languages = {{nowrap|None at [[Federal government of Mexico|federal level]]       |De facto: [[Spanish language|Spanish]]{{ref label|engoffbox|b|}}}}
|languages_type = [[National language]]
|languages = [[Mexican Spanish|Spanish]]{{ref label|engfactobox|b}}
|demonym = [[Mexican people|Mexican]]
|government_type = {{nowrap|[[Federalism|Federal]] [[Presidential system|presidential]]<br/>{{raise|0.13em|[[Republic|constitutional republic]]<ref>{{cite web |format=PDF |location=MX Q|url=http://www.scjn.gob.mx/SiteCollectionDocuments/PortalSCJN/RecJur/BibliotecaDigitalSCJN/PublicacionesSupremaCorte/Political_constitucion_of_the_united_Mexican_states_2008.pdf |archiveurl=https://web.archive.org/web/20110511194922/http://www.scjn.gob.mx/SiteCollectionDocuments/PortalSCJN/RecJur/BibliotecaDigitalSCJN/PublicacionesSupremaCorte/Political_constitucion_of_the_united_Mexican_states_2008.pdf |archivedate=May 11, 2011 |title=Political Constitution of the United Mexican States, title 2, article 40 |publisher=SCJN |accessdate=August 14, 2010}}</ref><!--end nowrap:-->}}<!--end raise:-->}}
|leader_title1 = [[President of Mexico|President]]
|leader_name1 = [[Enrique Peña Nieto]]
|leader_title2 = [[Senate of Mexico|President of the Senate]]
|leader_name2 = [[Roberto Gil Zuarth]]
|leader_title3 = [[Chamber of Deputies (Mexico)|President of the Chamber of Deputies]]
|leader_name3 = [[Jesús Zambrano Grijalva]]
|legislature = [[Congress of the Union|Congress]]
|upper_house = [[Senate of the Republic (Mexico)|Senate]]
|lower_house = [[Chamber of Deputies (Mexico)|Chamber of Deputies]]
|sovereignty_type = [[Mexican War of Independence|Independence]]
|sovereignty_note = from [[Spain]]
|established_event1 = [[Grito de Dolores|Declared]]
|established_date1 = September 16, 1810<ref name="Castro2000">{{cite book|author=Rafaela Castro|title=Chicano Folklore: A Guide to the Folktales, Traditions, Rituals and Religious Practices of Mexican Americans|url=https://books.google.com/books?id=WdzY7YjhRroC&pg=PA83|year=2000|publisher=Oxford University Press|isbn=978-0-19-514639-4|page=83}}</ref>
|established_event2 = [[Declaration of Independence of the Mexican Empire|Consummated]]
|established_date2 = September 27, 1821
|established_event3 = [[Spanish American wars of independence#New Spain and Central America|Recognized]]
|established_date3 = December 28, 1836
|established_event4 = [[1824 Constitution of Mexico|First constitution]]
|established_date4 = October 4, 1824
|established_event5 = [[Federal Constitution of the United Mexican States of 1857|Second constitution]]
|established_date5 = February 5, 1857
|established_event6 = [[Constitution of Mexico|Current constitution]]
|established_date6 = February 5, 1917
|area_km2 = 1,972,550
|area_footnote =
|area_rank = 13th
|area_sq_mi = 761,606
|percent_water = 2.5
|population_estimate = 119,530,753<ref name="Encuesta Intercensal 2015">{{cite web|title=Principales resultados de la Encuesta Intercensal 2015 Estados Unidos Mexicanos |url=http://www.inegi.org.mx/est/contenidos/proyectos/encuestas/hogares/especiales/ei2015/doc/eic2015_resultados.pdf |publisher=[[INEGI]] |accessdate=December 9, 2015 |pages=1, 77 |deadurl=yes |archiveurl=https://web.archive.org/web/20151210212235/http://www.inegi.org.mx/est/contenidos/proyectos/encuestas/hogares/especiales/ei2015/doc/eic2015_resultados.pdf |archivedate=December 10, 2015 |df=mdy }}</ref>
|population_estimate_year = 2015
|population_estimate_rank = 11th
|population_density_km2 =61
|population_density_sq_mi = 157
|population_density_rank = 142nd
|GDP_PPP = {{nowrap|$2.406 trillion<ref name="imf-mx">{{cite web |url=http://www.imf.org/external/pubs/ft/weo/2017/01/weodata/weorept.aspx?sy=2015&ey=2022&scsm=1&ssd=1&sort=country&ds=.&br=1&pr1.x=43&pr1.y=10&c=273&s=NGDPD%2CNGDPDPC%2CPPPGDP%2CPPPPC&grp=0&a= |title=Mexico |publisher=International Monetary Fund |accessdate=May 12, 2017}}</ref><!--end nowrap:-->}}
|GDP_PPP_year = 2017
|GDP_PPP_rank = 11th
|GDP_PPP_per_capita = $19,480.51<ref name="imf-mx"/>
|GDP_PPP_per_capita_rank = 64th
|GDP_nominal = {{nowrap|$987.3 billion<ref name="imf-mx"/>}}
|GDP_nominal_year = 2017
|GDP_nominal_rank = 16th
|GDP_nominal_per_capita = $7,993.17<ref name="imf-mx"/>
|GDP_nominal_per_capita_rank = 69th
|Gini = 48.2 <!--number only-->
|Gini_year = 2014
|Gini_change =  <!--increase/decrease/steady-->
|Gini_ref = <ref name="wb-gini">{{cite web |url=http://data.worldbank.org/indicator/SI.POV.GINI?locations=MX |title=Gini Index |publisher=[[World Bank]] |accessdate=November 9, 2016}}</ref>
|Gini_rank =
|HDI = 0.762 <!--number only-->
|HDI_year = 2015<!-- Please use the year to which the data refers, not the publication year-->
|HDI_change = increase <!--increase/decrease/steady-->
|HDI_ref = <ref name="HDI">{{cite web |url=http://hdr.undp.org/sites/default/files/2016_human_development_report.pdf |title=2016 Human Development Report |year=2016 |accessdate=March 23, 2017 |publisher=United Nations Development Programme}}</ref>
|HDI_rank = 77th
|currency = [[Mexican peso|Peso]]
|currency_code = MXN
|time_zone = ''See'' [[Time in Mexico]]
|utc_offset = −8 to −5
|utc_offset_DST = −7 to −5
|DST_note =
|time_zone_DST = varies
|antipodes =
|date_format =
|drives_on = right
|calling_code = [[+52]]
|iso3166code =
|cctld = [[.mx]]
|footnote_a = Article 4.° of the General Law of Linguistic Rights of the Indigenous Peoples.<ref>{{cite web |url=http://www.inali.gob.mx/pdf/LGDLPI.pdf |title=General Law of Linguistic Rights of the Indigenous Peoples |author=INALI |date=March 13, 2003 |accessdate=November 7, 2010}}</ref>
|footnote_b = {{note|engfactobox}} Spanish is the ''[[de facto]]'' official language of the Mexican federal government.
|recognized_regional_languages     =
{{hlist |[[Spanish language|Spanish]]<br>68 [[Languages of Mexico|native language groups]].<ref>{{cite web|url=http://www.inali.gob.mx/clin-inali/ |title=Catálogo de las lenguas indígenas nacionales: Variantes lingüísticas de México con sus autodenominaciones y referencias geoestadísticas |publisher=Inali.gob.mx |accessdate=July 18, 2014}}</ref>}}
|religion = {{ublist |item_style=white-space:nowrap; |83% [[Roman Catholicism]] |10% other Christian |0.2% other religion |5% [[Irreligion|no religion]] |3% unspecified<ref name="2010-census"/> }}
|area_magnitude = 1 E12
|area =
}}

'''Mexico''' ({{lang-es|México}}, {{IPA-es|ˈmexiko|pron|es-mx-México.ogg}}), officially the '''United Mexican States''' ({{lang-es|Estados Unidos Mexicanos|links=no}}, {{Audio|Es-mx-Estados Unidos Mexicanos.ogg|listen}}),<!-- Note: The only official name found in documents is "Estados Unidos Mexicanos" NOT "Estados Unidos de México" (which is not formally recognized); they do not mean the same thing so please don't add it. --><ref>{{cite news |last=Romo |first=Rafael |title=After nearly 200 years, Mexico may make the name official |url=http://www.cnn.com/2012/11/22/world/americas/mexico-name-change/index.html?hpt=hp_t3 |newspaper=CNN|date=November 23, 2012}}</ref><ref>{{cite web|url=http://embamex.sre.gob.mx/eua/index.php/en/about-mexico |title=About Mexico |publisher=Embajada de Mexico en Estados Unidos (Mexican Embassy in the United States) |date=December 3, 2012 |accessdate=July 17, 2013 |deadurl=yes |archiveurl=https://web.archive.org/web/20131202234006/http://embamex.sre.gob.mx/eua/index.php/en/about-mexico |archivedate=December 2, 2013 |df=mdy-all }}</ref><ref name="presidencia.gob.mx">{{cite web |url=http://www.presidencia.gob.mx/index.php?DNA=91 |publisher=Presidency of Mexico |title=Official name of the country|date=March 31, 2005 |accessdate=May 30, 2010}}</ref><ref name="cia.gov"/> is a [[federal republic]] in the southern portion of North America. It is [[Borders of Mexico|bordered]] to the north by the [[United States]]; to the south and west by the [[Pacific Ocean]]; to the southeast by [[Guatemala]], [[Belize]], and the [[Caribbean Sea]]; and to the east by the [[Gulf of Mexico]].<ref>Merriam-Webster's Geographical Dictionary, 3rd ed., Springfield, Massachusetts, USA, Merriam-Webster; p. 733</ref> Covering almost two million square kilometers (over 760,000&nbsp;sq&nbsp;mi),<ref name="cia.gov">{{CIA World Factbook link|mx|Mexico}}</ref> Mexico is the sixth largest country in the Americas by total area and the [[List of countries by area|13th largest independent nation]] in the world.

With an estimated population of over 120 million,<ref name="INEGI 2010 Census Statistics">{{cite web|url=http://www.inegi.org.mx/inegi/contenidos/espanol/prensa/comunicados/rpcpyv10.asp |title=INEGI 2010 Census Statistics |publisher=www.inegi.org.mx |accessdate=November 25, 2010 |deadurl=yes |archiveurl=https://web.archive.org/web/20110108101543/http://www.inegi.org.mx/inegi/contenidos/espanol/prensa/comunicados/rpcpyv10.asp |archivedate=January 8, 2011 |df=mdy-all }}</ref> Mexico is the [[List of countries by population|eleventh most populous]] country and the [[Hispanophone#Hispanosphere|most populous Spanish-speaking]] country in the world while being the second most populous country in [[Latin America]]. Mexico is a federation comprising 31 [[States of Mexico|states]] and a [[Mexico City|special federal entity]] that is also its capital and [[List of cities in Mexico#Largest cities|most populous city]]. Other [[Metropolitan areas of Mexico|metropolises]] include [[Guadalajara Metropolitan Area|Guadalajara]], [[León, Guanajuato|León]], [[Monterrey Metropolitan area|Monterrey]], [[Metropolitan area of Puebla|Puebla]], [[Greater Toluca|Toluca]], and [[Tijuana metropolitan area|Tijuana]].

[[Pre-Columbian Mexico]] was home to many advanced [[Mesoamerica]]n civilizations, such as the [[Olmec]],  [[Toltec]], [[Teotihuacan]], [[Zapotec civilization|Zapotec]], [[Maya civilization|Maya]] and [[Aztec]] before first contact with [[Europe]]ans. In 1521, the [[Spanish Empire]] [[Spanish conquest of the Aztec Empire|conquered and colonized]] the territory from its base in [[Mexico-Tenochtitlan]], which was administered as the [[New Spain|viceroyalty of New Spain]]. Three centuries later, this territory became Mexico following recognition in 1821 after the colony's [[Mexican War of Independence]]. The tumultuous post-independence period was characterized by [[Economic history of Mexico#Independence|economic instability]] and many political changes. The [[Mexican–American War]] (1846–48) led to the [[Territorial evolution of Mexico|territorial cession]] of the extensive northern territories to the United States. The [[Pastry War]], the [[Franco-Mexican War]], a [[Reform War|civil war]], [[Emperor of Mexico|two empires]] and [[List of Presidents of Mexico#Porfiriato|a domestic dictatorship]] occurred through the 19th century. The dictatorship was overthrown in the [[Mexican Revolution]] of 1910, which culminated with the promulgation of the [[Constitution of Mexico|1917 Constitution]] and the emergence of the country's current [[Politics of Mexico|political system]].

"""

wp = WikiParser(None)
wp.article_callback("Mexico",doc)