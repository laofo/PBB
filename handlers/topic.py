#coding=utf-8

import tornado.web
import time
from . import BaseHandler
from bson.objectid import ObjectId
from .utils import make_content


class TopicListHandler(BaseHandler):
    def get(self):
        topics = self.db.topics.find(sort=[('last_reply_time', -1)])
        topics_count = topics.count()
        p = int(self.get_argument('p', 1))
        self.render('topic/list.html', topics=topics,
            topics_count=topics_count, p=p)


class TopicHandler(BaseHandler):
    def get(self, topic_id):
        topic = self.get_topic(topic_id)
        if self.current_user:
            self.db.notifications.update({
                'topic': ObjectId(topic_id),
                'to': self.current_user['name_lower']
            }, {'$set': {'read': True}}, multi=True)
            if 'read' in topic:
                self.db.topics.update({'_id': ObjectId(topic_id)},
                    {'$addToSet': {'read': self.current_user['name_lower']}})
            else:
                self.db.topics.update({'_id': ObjectId(topic_id)},
                    {'$set': {'read': [self.current_user['name_lower']]}})
        replies = self.db.replies.find({'topic': topic_id},
            sort=[('index', 1)])
        replies_count = replies.count()
        p = int(self.get_argument('p', 1))
        if p < 1:
            p = 1
        self.render('topic/topic.html', topic=topic,
            replies=replies, replies_count=replies_count,
            p=p)


class CreateHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('topic/create.html')


class ReplyHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self, topic_id):
        content = self.get_argument('content', None)
        if not content:
            self.flash('Please fill the required field')
        elif len(content) > 20000:
            self.flash("The content is too lang")
        if self.messages:
            self.redirect('/topic/%s' % topic_id)
            return
        reply = self.db.replies.find_one({
            'topic': topic_id,
            'content': content,
            'author': self.current_user['name']
        })
        if reply:
            self.redirect('/topic/%s' % topic_id)
            return
        index = self.db.topics.find_and_modify({'_id': ObjectId(topic_id)},
            update={'$inc': {'index': 1}})['index'] + 1
        time_now = time.time()
        content_html = make_content(content)
        self.send_notification(content_html, topic_id)
        source = self.get_source()
        data = {
            'content': content,
            'content_html': content_html,
            'author': self.current_user['name'],
            'topic': topic_id,
            'created': time_now,
            'modified': time_now,
            'index': index,
        }
        if source:
            data['source'] = source
        self.db.replies.insert(data)
        self.db.topics.update({'_id': ObjectId(topic_id)},
            {'$set': {'last_reply_time': time_now,
                'last_reply_by': self.current_user['name'],
                'read': [self.current_user['name_lower']]}})
        reply_nums = self.db.replies.find({'topic': topic_id}).count()
        last_page = self.get_page_num(reply_nums,
            self.settings['replies_per_page'])
        self.redirect('/topic/%s?p=%s' % (topic_id, last_page))


class RemoveHandler(BaseHandler):
    def get(self, topic_id):
        self.check_role(owner_name=self.current_user['name'])
        members = self.db.members.find({'like': topic_id})
        for member in members:
            member['like'].remove(topic_id)
            self.db.members.save(member)
        topic_id = ObjectId(topic_id)
        self.db.topics.remove({'_id': topic_id})
        self.db.replies.remove({'topic': topic_id})
        self.db.notifications.remove({'topic': ObjectId(topic_id)})
        self.flash('Removed successfully', type='success')
        self.redirect('/')


class EditHandler(BaseHandler):
    def get(self, topic_id):
        topic = self.get_topic(topic_id)
        self.check_role(owner_name=topic['author'])
        node = self.get_node(topic['node'])
        self.render('topic/edit.html', topic=topic,
            node=node)

    def post(self, topic_id):
        topic = self.get_topic(topic_id)
        self.check_role(owner_name=topic['author'])
        title = self.get_argument('title', '')
        content = self.get_argument('content', '')
        topic['title'] = title
        topic['content'] = content
        if not (title and content):
            self.flash('Please fill the required field')
        if len(title) > 100:
            self.flash("The title is too long")
        if len(content) > 20000:
            self.flash("The content is too lang")
        if self.messages:
            self.render('topic/edit.html', topic=topic)
            return
        topic['modified'] = time.time()
        content = make_content(content)
        self.db.notifications.update({'content': topic['content_html'],
                                      'topic': ObjectId(topic_id)},
            {'$set': {'content': content}})
        topic['content_html'] = content
        self.db.topics.save(topic)
        self.flash('Saved successfully', type='success')
        self.redirect('/topic/%s' % topic_id)


class MoveHandler(BaseHandler):
    def get(self, topic_id):
        topic = self.get_topic(topic_id)
        self.render('topic/move.html', topic=topic)

    def post(self, topic_id):
        node_name = self.get_argument('node', '')
        import logging
        logging.info(node_name)
        node = self.get_node(node_name.lower())
        self.db.topics.update({'_id': ObjectId(topic_id)},
                {'$set': {'node': node['name']}})
        self.flash('Moved successfully', type='success')
        self.redirect('/topic/%s' % topic_id)


class EditReplyHandler(BaseHandler):
    def get(self, reply_id):
        reply = self.db.replies.find_one({'_id': ObjectId(reply_id)})
        if not reply:
            raise tornado.web.HTTPError(404)
        self.check_role(owner_name=reply['author'])
        self.render('topic/edit_reply.html', reply=reply)

    def post(self, reply_id):
        reply = self.db.replies.find_one({'_id': ObjectId(reply_id)})
        if not reply:
            raise tornado.web.HTTPError(404)
        self.check_role(owner_name=reply['author'])
        content = self.get_argument('content', '')
        reply['content'] = content
        if not content:
            self.flash('Please fill the required field')
        elif len(content) > 20000:
            self.flash("The content is too lang")
        if self.messages:
            self.render('topic/edit_reply.html', reply=reply)
            return
        reply['modified'] = time.time()
        content = make_content(content)
        self.db.notifications.update({'content': reply['content_html']},
                {'$set': {'content': content}})
        reply['content_html'] = content
        self.db.replies.save(reply)
        self.flash('Saved successfully', type='success')
        self.redirect(self.get_argument('next', '/'))


class RemoveReplyHandler(BaseHandler):
    def get(self, reply_id):
        self.check_role(owner_name=self.current_user['name'])
        reply = self.db.replies.find_one({'_id': ObjectId(reply_id)})
        if not reply:
            raise tornado.web.HTTPError(404)
        self.db.notifications.remove({
            'from': reply['author'].lower(),
            'content': reply['content_html'],
        }, multi=True)
        self.db.replies.remove({'_id': ObjectId(reply_id)})
        self.flash('Removed successfully', type='success')
        self.redirect(self.get_argument('next', '/'))


class TopicList(tornado.web.UIModule):
    def render(self, topics):
        return self.render_string("topic/modules/list.html", topics=topics)


class Paginator(tornado.web.UIModule):
    def render(self, p, perpage, count, base_url):
        return self.render_string("topic/modules/paginator.html", p=p,
            perpage=perpage, count=count, base_url=base_url)

handlers = [
    (r'/', TopicListHandler),
    (r'/topic', TopicListHandler),
    (r'/topic/create', CreateHandler),
    (r'/topic/(\w+)', TopicHandler),
    (r'/topic/(\w+)/edit', EditHandler),
    (r'/topic/(\w+)/reply', ReplyHandler),
    (r'/topic/(\w+)/remove', RemoveHandler),
    (r'/topic/(\w+)/move', MoveHandler),
    (r'/reply/(\w+)/edit', EditReplyHandler),
    (r'/reply/(\w+)/remove', RemoveReplyHandler),
]

ui_modules = {
    'topic_list': TopicList,
    'paginator': Paginator,
}
