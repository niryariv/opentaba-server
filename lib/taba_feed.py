# -*- coding: utf-8 -*-

from werkzeug.contrib.atom import AtomFeed, FeedEntry
from werkzeug.contrib.atom import _make_text_block, format_iso8601
from werkzeug.utils import escape


class TabaAtomFeed(AtomFeed):
    """
    An override of werkzeug.contrib.atom.AtomFeed so that we are
    able to add a namespace and work with TabaFeedEntry instead
    of normal FeedEntry
    """
    
    def add(self, *args, **kwargs):
        """
        Only changed to work with TabaFeedEntry instead of FeedEntry
        """
        if len(args) == 1 and not kwargs and isinstance(args[0], TabaFeedEntry):
            self.entries.append(args[0])
        else:
            kwargs['feed_url'] = self.feed_url
            self.entries.append(TabaFeedEntry(*args, **kwargs))
    
    
    def generate(self):
        """
        Changed to yield the Public Knowledge Workshop's pkw
        namespace alongside the normal Atom one
        """
        # atom demands either an author element in every entry or a global one
        if not self.author:
            if False in map(lambda e: bool(e.author), self.entries):
                self.author = ({'name': 'Unknown author'},)

        if not self.updated:
            dates = sorted([entry.updated for entry in self.entries])
            self.updated = dates and dates[-1] or datetime.utcnow()

        yield u'<?xml version="1.0" encoding="utf-8"?>\n'
        yield u'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:pkw="http://hasadna.org.il/rss/1.0/dtd">\n'
        yield '  ' + _make_text_block('title', self.title, self.title_type)
        yield u'  <id>%s</id>\n' % escape(self.id)
        yield u'  <updated>%s</updated>\n' % format_iso8601(self.updated)
        if self.url:
            yield u'  <link href="%s" />\n' % escape(self.url, True)
        if self.feed_url:
            yield u'  <link href="%s" rel="self" />\n' % \
                escape(self.feed_url, True)
        for link in self.links:
            yield u'  <link %s/>\n' % ''.join('%s="%s" ' % \
                (k, escape(link[k], True)) for k in link)
        for author in self.author:
            yield u'  <author>\n'
            yield u'    <name>%s</name>\n' % escape(author['name'])
            if 'uri' in author:
                yield u'    <uri>%s</uri>\n' % escape(author['uri'])
            if 'email' in author:
                yield '    <email>%s</email>\n' % escape(author['email'])
            yield '  </author>\n'
        if self.subtitle:
            yield '  ' + _make_text_block('subtitle', self.subtitle,
                                          self.subtitle_type)
        if self.icon:
            yield u'  <icon>%s</icon>\n' % escape(self.icon)
        if self.logo:
            yield u'  <logo>%s</logo>\n' % escape(self.logo)
        if self.rights:
            yield '  ' + _make_text_block('rights', self.rights,
                                          self.rights_type)
        generator_name, generator_url, generator_version = self.generator
        if generator_name or generator_url or generator_version:
            tmp = [u'  <generator']
            if generator_url:
                tmp.append(u' uri="%s"' % escape(generator_url, True))
            if generator_version:
                tmp.append(u' version="%s"' % escape(generator_version, True))
            tmp.append(u'>%s</generator>\n' % escape(generator_name))
            yield u''.join(tmp)
        for entry in self.entries:
            for line in entry.generate():
                yield u'  ' + line
        yield u'</feed>\n'


class TabaFeedEntry(FeedEntry):
    """
    An override of werkzeug.contrib.atom.FeedEntry so that we can add
    a pkw:tags for our notification center
    """
    
    def __init__(self, title=None, content=None, feed_url=None, **kwargs):
        """
        Changed so that we have an extra value - tags
        """
        super(TabaFeedEntry, self).__init__(title, content, feed_url, **kwargs)
        
        self.tags = kwargs.get('tags', [])
    
    
    def generate(self):
        """
        Changed to yield the list of tags as comma-delimited list
        alongside all other normal values
        """
        base = ''
        if self.xml_base:
            base = ' xml:base="%s"' % escape(self.xml_base, True)
        yield u'<entry%s>\n' % base
        yield u'  ' + _make_text_block('title', self.title, self.title_type)
        yield u'  <id>%s</id>\n' % escape(self.id)
        yield u'  <updated>%s</updated>\n' % format_iso8601(self.updated)
        if self.published:
            yield u'  <published>%s</published>\n' % \
                  format_iso8601(self.published)
        if self.url:
            yield u'  <link href="%s" />\n' % escape(self.url)
        for author in self.author:
            yield u'  <author>\n'
            yield u'    <name>%s</name>\n' % escape(author['name'])
            if 'uri' in author:
                yield u'    <uri>%s</uri>\n' % escape(author['uri'])
            if 'email' in author:
                yield u'    <email>%s</email>\n' % escape(author['email'])
            yield u'  </author>\n'
        for link in self.links:
            yield u'  <link %s/>\n' % ''.join('%s="%s" ' % \
                (k, escape(link[k], True)) for k in link)
        yield u'  <pkw:tags>%s</pkw:tags>\n' % ','.join(self.tags)
        if self.summary:
            yield u'  ' + _make_text_block('summary', self.summary,
                                           self.summary_type)
        if self.content:
            yield u'  ' + _make_text_block('content', self.content,
                                           self.content_type)
        yield u'</entry>\n'
