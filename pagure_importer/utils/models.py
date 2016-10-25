# -*- coding: utf-8 -*-
import uuid


class Issue():
    ''' Represents an Issue '''

    def __init__(
            self, id, title, content,
            status, date_created, user, private, attachment, tags,
            depends, blocks, assignee, close_status, comments=None,
            milestone=None, custom_fields=None):

        self.id = id
        self.title = title
        self.content = content
        self.status = status
        self.close_status = close_status
        self.date_created = date_created
        self.user = user
        self.private = private
        self.attachment = attachment
        self.tags = tags
        self.depends = depends
        self.blocks = blocks
        self.assignee = assignee
        self.comments = comments
        self.uid = uuid.uuid4().hex
        self.milestone = milestone
        self.custom_fields = custom_fields if custom_fields else []

    def to_json(self):
        ''' Returns a dictionary representation of the issue.

        '''
        output = {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'status': self.status,
            'close_status': self.close_status,
            'date_created': self.date_created,
            'user': self.user,
            'private': self.private,
            'tags': self.tags,
            'depends': self.depends,
            'blocks': self.blocks,
            'assignee': self.assignee,
            'comments': self.comments,
            'milestone': self.milestone,
            'custom_fields': self.custom_fields,
        }

        return output

    @property
    def isa(self):
        return 'issue'


class IssueComment():
    ''' Represent a comment for an issue '''

    def __init__(
            self, id, comment, date_created,
            user, attachment, parent=None, edited_on=None, editor=None):

        self.id = id
        self.comment = comment
        self.parent = parent
        self.date_created = date_created
        self.user = user
        self.attachment = attachment
        self.edited_on = edited_on
        self.editor = editor

    def to_json(self):
        ''' Returns a dictionary representation of the issue. '''

        output = {
            'id': self.id,
            'comment': self.comment,
            'parent': self.parent,
            'date_created': self.date_created,
            'user': self.user,
            'edited_on': self.edited_on if self.edited_on else None,
            'editor': self.editor or None
        }

        return output


class User():
    ''' Represents a User '''

    def __init__(
            self, name, emails,
            fullname=None):
        self.name = name
        self.fullname = fullname
        self.emails = emails

    def to_json(self):
        ''' Return a representation of the User in a dictionary. '''

        output = {
            'name': self.name,
            'fullname': self.fullname,
            'emails': self.emails
        }

        return output
