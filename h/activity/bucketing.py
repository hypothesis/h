"""Code for bucketing annotations by time frame and document."""

from __future__ import unicode_literals

import collections
import datetime

from pyramid import i18n


_ = i18n.TranslationStringFactory(__package__)


class Timeframe(object):
    """
    A timeframe into which annotations can be bucketed.

    Any annotations that are added into a timeframe bucket will be further
    bucketed by their documents, within the timeframe.

    """

    def __init__(self, label, cutoff_time):
        self.label = label
        self.cutoff_time = cutoff_time
        self.document_buckets = collections.OrderedDict()

    def append(self, annotation):
        """
        Append an annotation to its document bucket in this timeframe.

        This doesn't check whether the annotation's time is within this
        timeframe, the caller is required to do that.

        """
        document_bucket = self.document_buckets.get(annotation.document)

        if document_bucket is None:
            document_bucket = []
            self.document_buckets[annotation.document] = document_bucket

        document_bucket.append(annotation)

    def within_cutoff(self, annotation):
        """
        Return True if annotation is within this timeframe's cutoff time.

        Return ``True`` if the given annotation is newer than this timeframe's
        cutoff time, meaning that the annotation can be bucketed into this
        timeframe.

        Return ``False`` if the given annotation is older than this timeframe's
        cutoff time and the next timeframe needs to be generated in order to
        bucket the annotation.

        Note that this method returning ``True`` does not necessarily mean that
        the annotation *should* be bucketed in this timeframe, since the
        annotation may also be within the cutoff times of previous timeframes.
        It's up to the caller to handle this.

        """
        return annotation.updated >= self.cutoff_time

    def __repr__(self):
        return '{class_} "{label}" with {n} document buckets'.format(
            class_=self.__class__, label=self.label,
            n=len(self.document_buckets))


class TimeframeGenerator(object):

    def __init__(self):
        self.timeframes = [
            Timeframe(_("Last 7 days"), utcnow() - datetime.timedelta(days=7)),
        ]

    def next(self, annotation):
        """
        Return the next timeframe to be used for bucketing annotations.

        :param annotation: the next annotation to be bucketed, the returned
            timeframe is guaranteed to be the correct timeframe for this
            annotation

        """
        while self.timeframes:
            timeframe = self.timeframes.pop(0)
            if timeframe.within_cutoff(annotation):
                return timeframe

        cutoff_time = datetime.datetime(year=annotation.updated.year,
                                        month=annotation.updated.month,
                                        day=1)
        timeframe = Timeframe(annotation.updated.strftime('%b %Y'),
                              cutoff_time)
        return timeframe


def bucket(annotations):
    """
    Return the given annotations bucketed by timeframe and document.

    :param annotations: A chronologically-ordered list of annotations.
        This list of annotations is assumed to be sorted most recently updated
        annotation first, otherwise the bucketing algorithm will not return the
        right results.

    :rtype: chronologically-ordered list of Timeframe objects

    """
    if not annotations:
        return []

    generator = TimeframeGenerator()
    timeframes = [generator.next(annotations[0])]

    for annotation in annotations:
        if not timeframes[-1].within_cutoff(annotation):
            timeframes.append(generator.next(annotation))
        timeframes[-1].append(annotation)

    return timeframes


def utcnow():
    return datetime.datetime.utcnow()
