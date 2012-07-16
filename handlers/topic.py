#coding=utf-8

import tornado.web
import time
from . import BaseHandler
from pymongo.objectid import ObjectId
from .utils import make_content


class TopicListHandler(BaseHandler):
    def get(self):
        topics = self.db.topics.find(sort=[('created', -1)])
        topics_count = topics.count()
        p = int(self.get_argument('p', 1))
        self.render('topic/list.html', topics=topics,
            topics_count=topics_count, p=p)


class TopicHandler(BaseHandler):
    def get(self, topic_id):
        topic = self.get_topic(topic_id)
        replies = self.db.replies.find({'topic': topic_id},
            sort=[('created', 1)])
        replies_count = replies.count()
        p = int(self.get_argument('p', 1))
        self.render('topic/topic.html', topic=topic,
            replies=replies, replies_count=replies_count,
            p=p)


class ReplyHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self, topic_id):
        self.check_role(role_min=1)
        content = self.get_argument('content', None)
        if not content:
            self.flash('Please fill the required field')
            self.redirect('/topic/%s' % topic_id)
            return
        reply = self.db.replies.find_one({
            'topic': topic_id,
            'content': content,
            'author': self.current_user['_id']
        })
        if reply:
            self.redirect('/topic/%s' % topic_id)
            return
        index = self.db.topics.find_and_modify({'_id': ObjectId(topic_id)},
            update={'$inc': {'index': 1}})['index'] + 1
        time_now = time.time()
        self.db.replies.insert({
            'content': content,
            'content_html': make_content(content),
            'author': self.current_user['name'],
            'topic': topic_id,
            'created': time_now,
            'modified': time_now,
            'index': index,
        })
        self.redirect('/topic/%s' % topic_id)


class RemoveHandler(BaseHandler):
    def get(self, topic_id):
        self.check_role()
        self.db.topics.remove({'_id': ObjectId(topic_id)})
        self.db.replies.remove({'topic': topic_id})
        self.flash('Removed successfully')
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
        if self.messages:
            self.render('topic/edit.html', topic=topic)
            return
        topic['modified'] = time.time()
        topic['content_html'] = make_content(content)
        self.db.topics.save(topic)
        self.flash('Saved successfully', type='success')
        self.redirect('/topic/%s' % topic_id)


class MoveHandler(BaseHandler):
    def get(self, topic_id):
        pass
        #topic = self.get_topic(topic_id)
        #self.render('topic/move.html', topic=topic)

    def post(self, topic_id):
        pass


class LikeHandler(BaseHandler):
    def get(self, topic_id):
        user_id = self.current_user['_id']
        self.db.members.update({'_id': user_id},
                {'$addToSet': {'like': topic_id}})
        self.redirect('/topic/' + topic_id)


class UnlikeHandler(BaseHandler):
    def get(self, topic_id):
        user = self.current_user
        user['like'].remove(topic_id)
        self.db.members.save(user)
        self.redirect('/topic/' + topic_id)


class TopicList(tornado.web.UIModule):
    def render(self, topics):
        return self.render_string("topic/modules/list.html", topics=topics)

handlers = [
    (r'/', TopicListHandler),
    (r'/topic', TopicListHandler),
    (r'/topic/(\w+)', TopicHandler),
    (r'/topic/(\w+)/edit', EditHandler),
    (r'/topic/(\w+)/reply', ReplyHandler),
    (r'/topic/(\w+)/remove', RemoveHandler),
    (r'/topic/(\w+)/move', MoveHandler),
    (r'/topic/(\w+)/like', LikeHandler),
    (r'/topic/(\w+)/unlike', UnlikeHandler),
]

ui_modules = {
    'topic_list': TopicList,
}