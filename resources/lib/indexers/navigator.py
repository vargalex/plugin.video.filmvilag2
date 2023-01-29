# -*- coding: utf-8 -*-

'''
    dmdamedia Addon
    Copyright (C) 2020

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
import os,sys,re,xbmc,xbmcgui,xbmcplugin, time, locale
import resolveurl as urlresolver
from resources.lib.modules import client, control
from resources.lib.modules.utils import py2_encode, py2_decode

if sys.version_info[0] == 3:
    import urllib.parse as urlparse
    from urllib.parse import quote_plus
else:
    import urlparse
    from urllib import quote_plus

sysaddon = sys.argv[0] ; syshandle = int(sys.argv[1])
addonFanart = control.addonInfo('fanart')
base_url = control.setting('base_url')

class navigator:
    def __init__(self):
        try:
            locale.setlocale(locale.LC_ALL, "")
        except:
            pass
        self.base_path = py2_decode(control.transPath(control.addonInfo('profile')))
        self.searchFileName = os.path.join(self.base_path, "search.history")

    def getCategories(self):
        url_content = client.request(base_url, error=True)
        mainMenu=client.parseDOM(url_content, 'menu')[0].strip()
        menuItems = client.parseDOM(mainMenu, 'li')
        self.addDirectoryItem('Keresés', 'search', '', 'DefaultFolder.png')
        for menuItem in menuItems:
            text = py2_encode(client.replaceHTMLCodes(client.parseDOM(menuItem, 'a')[0]))
            url = client.parseDOM(menuItem, 'a', ret='href')[0]
            if not text.startswith(('Kezdőlap', 'Kérjél', 'Támogatás', 'CHAT', 'Jogi nyilatkozat')):
                self.addDirectoryItem(text, 'articles&url=%s' % url, '', 'DefaultFolder.png')
        self.endDirectory()

    def getSearches(self):
        self.addDirectoryItem('Új keresés', 'newsearch', '', 'DefaultFolder.png')
        try:
            file = open(self.searchFileName, "r")
            olditems = file.read().splitlines()
            file.close()
            items = list(set(olditems))
            items.sort(key=locale.strxfrm)
            if len(items) != len(olditems):
                file = open(self.searchFileName, "w")
                file.write("\n".join(items))
                file.close()
            for item in items:
                self.addDirectoryItem(item, 'historysearch&search=%s' % (quote_plus(item)), '', 'DefaultFolder.png')
            if len(items) > 0:
                self.addDirectoryItem('Keresési előzmények törlése', 'deletesearchhistory', '', 'DefaultFolder.png') 
        except:
            pass   
        self.endDirectory()

    def deleteSearchHistory(self):
        if os.path.exists(self.searchFileName):
            os.remove(self.searchFileName)

    def doSearch(self):
        search_text = self.getText(u'Add meg a keresend\xF5 film c\xEDm\xE9t')
        if search_text != '':
            if not os.path.exists(self.base_path):
                os.mkdir(self.base_path)
            file = open(self.searchFileName, "a")
            file.write("%s\n" % search_text)
            file.close()
            self.getResults(search_text)

    def getArticles(self, url):
        url = "" if url == None else url
        url_content = client.request('%s/%s' % (base_url, url), error=True)
        articlesDiv = client.parseDOM(url_content, 'div', attrs={'id': 'articles'})[0]
        articles = client.parseDOM(articlesDiv, 'div', attrs={'class': 'article'})
        for article in articles:
            preview = client.parseDOM(article, 'div', attrs={'class': 'preview'})[0]
            href = client.parseDOM(article, 'a', ret='href')[0]
            thumb = '%s%s' % (base_url, client.parseDOM(article, 'img', ret='src')[0])
            heading3 = client.parseDOM(article, 'h3')[0]
            title = py2_encode(client.parseDOM(heading3, 'a')[0])
            editorArea = py2_encode(client.replaceHTMLCodes(client.parseDOM(article, 'div', attrs={'class': 'editor-area'})[0])).strip()
            matches = re.search(r'^(.*)>(.*), ([0-9]*) perc,(.*)([1-2][0-9]{3})(.*)$', editorArea, re.S)
            xtraInfo = re.search(r'^(.*)color: rgb\(255, 0, 0\)(.*)>(.*)</span>(.*)$', editorArea, re.S)
            extraInfo = ""
            if xtraInfo != None:
                extraInfo = " | [COLOR red]%s[/COLOR]" % xtraInfo.group(3)
            if matches != None:
                self.addDirectoryItem('%s (%s) | [COLOR limegreen]%s[/COLOR]%s' % (title, matches.group(5), matches.group(2), extraInfo), 'movie&url=%s&thumb=%s&duration=%s' % (href, quote_plus(thumb), quote_plus(matches.group(3))), thumb, 'DefaultMovies.png', meta={'title': title, 'duration': int(matches.group(3))*60, 'fanart': thumb})
            else:
                matches = re.search(r'^(.*)>(.*),(.*)([1-2][0-9]{3})(.*)$', editorArea, re.S)
                if matches != None:
                    self.addDirectoryItem('%s (%s) | [COLOR limegreen]%s[/COLOR]%s' % (title, matches.group(4), matches.group(2), extraInfo), 'movie&url=%s&thumb=%s&duration=%s' % (href, quote_plus(thumb), "0"), thumb, 'DefaultMovies.png', meta={'title': title, 'duration': 0, 'fanart': thumb})
                else:
                    self.addDirectoryItem('%s | %s' % (title, extraInfo), 'movie&url=%s&thumb=%s&duration=%s' % (href, quote_plus(thumb), "0"), thumb, 'DefaultMovies.png', meta={'title': title, 'duration': 0, 'fanart': thumb})
        listOfPages = client.parseDOM(articlesDiv, 'div', attrs={'class': 'list-of-pages'})
        if len(listOfPages) > 0:
            next = client.parseDOM(listOfPages, 'p', attrs={'class': 'next'})
            if len(next) > 0:
                nextPage = client.parseDOM(next, 'a', ret='href')
                if len(nextPage) > 0:
                    self.addDirectoryItem(u'[I]K\u00F6vetkez\u0151 oldal >>[/I]', 'articles&url=%s' % quote_plus(nextPage[0]), '', 'DefaultFolder.png')
        self.endDirectory('movies')

    def getResults(self, search_text):
        url_content = client.request(base_url, error=True)
        searchDiv = client.parseDOM(url_content, 'div', attrs={'id': 'search'})
        innerFrameDiv = client.parseDOM(searchDiv, 'div', attrs={'class': 'inner_frame'})
        searchURL = client.parseDOM(innerFrameDiv, 'form', ret='action')[0]
        uid = client.parseDOM(innerFrameDiv, 'input', attrs={'id': 'uid'}, ret='value')[0]
        url_content = client.request(searchURL, post="uid=%s&key=%s" % (uid, quote_plus(search_text)), error=True)
        searchResult = client.parseDOM(url_content, 'div', attrs={'class': 'search-results'})
        resultsUser = client.parseDOM(searchResult, 'div', attrs={'class': 'results-user'})
        ul = client.parseDOM(resultsUser, 'ul')
        if len(ul)>0:
            lis = client.parseDOM(ul, 'li')
            linkCount = 0
            for li in lis:
                href = client.parseDOM(li, 'a', ret='href')[0].replace('http://', 'https://').replace(base_url, '')
                if "filmkeres-es-hibas-link-jelentese.html" not in href and "miert-van-kevesebb-tartalom-mostanaban-az-oldalon-.html" not in href:
                    linkCount += 1
                    title = py2_encode(client.parseDOM(li, 'a')[0])
                    self.addDirectoryItem(title, 'movie&url=%s' % quote_plus(href), '', 'DefaultMovies.png')
            if linkCount>0:
                self.endDirectory('movies')
                return
        xbmcgui.Dialog().ok("OnlineFilmvilág2", "Nincs találat!")

    def getMovie(self, url, thumb, duration):
        url_content = client.request('%s%s' %(base_url, url), error=True)
        if 'class="locked' in url_content:
            password = control.setting('password')
            if password == '':
                password = self.getText(u'Add meg a Cinema World facebook oldalról\nüzenetben kapott kódot!', True)
                if password == '':
                    return
            url_content = client.request('%s%s' %(base_url, url), post="password=%s&submit=Küldés" % password, error=True)
            while 'class="locked' in url_content:
                password = self.getText(u'Hibás jelszó! Kérlek pontosan add meg a Cinema World\nfacebook oldalról üzenetben kapott kódot!', True)
                if password == '':
                    return
                url_content = client.request('%s%s' %(base_url, url), post="password=%s&submit=Küldés" % password, error=True)
            control.setSetting('password', password)
        article = client.parseDOM(url_content, 'div', attrs={'class': 'article'})[0]
        header = client.parseDOM(article, 'h2')[0]
        title = client.parseDOM(header, 'span')[0]
        editorArea = client.parseDOM(article, 'div', attrs={'class': 'editor-area'})[0]
        plot = ''
        """
        paragraphs = client.parseDOM(editorArea, 'p')
        for paragraph in paragraphs:
            if "<span" in paragraph:
                plot = "%s%s%s" % (plot, "" if plot == "" else "\n", client.replaceHTMLCodes(client.parseDOM(paragraph, 'span')[0]))    
            elif "</" not in paragraph:
                plot = "%s%s%s" % (plot, "" if plot == "" else "\n", client.replaceHTMLCodes(paragraph))
        #plot = plot.replace("&nbsp;", "")
        """
        matches=re.findall(r'(?:.*)rgb\(50, 50, 50\)(?:.*)">([^<]*)<(?:.*)', editorArea)
        if matches != None:
            plot = '\n'.join(matches)
            plot = plot.replace('&nbsp;', '')
        if len(plot.replace(' ', '').replace('\t', '').replace('\r', '').replace('\n', '')) == 0:
            paragraphs = client.parseDOM(editorArea, 'p')
            for paragraph in paragraphs:
                if "<span" in paragraph:
                    plot = "%s%s%s" % (plot, "" if plot == "" else "\n", client.replaceHTMLCodes(client.parseDOM(paragraph, 'span')[0]))    
                elif "</" not in paragraph:
                    plot = "%s%s%s" % (plot, "" if plot == "" else "\n", client.replaceHTMLCodes(paragraph))
            plot = plot.replace('&nbsp;', '')
        matches = re.search(r'<img alt([^>]*)>(.*)', plot, re.S)
        if matches:
            plot = matches.group(2)
        sources = client.parseDOM(editorArea, 'iframe', ret='src')
        sources2 = client.parseDOM(editorArea, 'a', ret='href')
        banner = thumb
        sourceCnt = 0
        for src in sources+sources2:
            sourceCnt+=1
            self.addDirectoryItem('%s | [B]%s[/B]' % (format(sourceCnt, '02'), urlparse.urlparse(src).hostname), 'playmovie&url=%s' % (quote_plus(src)), thumb, 'DefaultMovies.png', isFolder=False, meta={'title': title, 'plot': plot, 'duration': int(duration)*60}, banner=banner)
        self.endDirectory('movies')

    def playmovie(self, url):
        if "http" not in url:
            url = ("https:%s" % url)
        xbmc.log('filmvilag: resolving url: %s' % url, xbmc.LOGINFO)
        try:
            direct_url = urlresolver.resolve(url)
            if direct_url:
                direct_url = py2_encode(direct_url)
            else:
                direct_url = url
        except Exception as e:
            xbmcgui.Dialog().notification(urlparse.urlparse(url).hostname, str(e))
            return
        if direct_url:
            xbmc.log('filmvilag: playing URL: %s' % direct_url, xbmc.LOGINFO)
            play_item = xbmcgui.ListItem(path=direct_url)
            xbmcplugin.setResolvedUrl(syshandle, True, listitem=play_item)

    def addDirectoryItem(self, name, query, thumb, icon, context=None, queue=False, isAction=True, isFolder=True, Fanart=None, meta=None, banner=None):
        url = '%s?action=%s' % (sysaddon, query) if isAction == True else query
        if thumb == '': thumb = icon
        cm = []
        if queue == True: cm.append((queueMenu, 'RunPlugin(%s?action=queueItem)' % sysaddon))
        if not context == None: cm.append((py2_encode(context[0]), 'RunPlugin(%s?action=%s)' % (sysaddon, context[1])))
        item = xbmcgui.ListItem(label=name)
        item.addContextMenuItems(cm)
        item.setArt({'icon': thumb, 'thumb': thumb, 'poster': thumb, 'banner': banner})
        if Fanart == None: Fanart = addonFanart
        item.setProperty('Fanart_Image', Fanart)
        if isFolder == False: item.setProperty('IsPlayable', 'true')
        if not meta == None: item.setInfo(type='Video', infoLabels = meta)
        xbmcplugin.addDirectoryItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)


    def endDirectory(self, type='addons'):
        xbmcplugin.setContent(syshandle, type)
        #xbmcplugin.addSortMethod(syshandle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(syshandle, cacheToDisc=True)

    def getText(self, title, hidden=False):
        search_text = ''
        keyb = xbmc.Keyboard('', title, hidden)
        keyb.doModal()

        if (keyb.isConfirmed()):
            search_text = keyb.getText()

        return search_text
