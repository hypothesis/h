"""Factory classes for easily generating test objects."""

from tests.common.factories import requests_ as requests
from tests.common.factories.activation import Activation
from tests.common.factories.annotation import Annotation
from tests.common.factories.annotation_metadata import AnnotationMetadata
from tests.common.factories.annotation_slim import AnnotationSlim
from tests.common.factories.auth_client import AuthClient, ConfidentialAuthClient
from tests.common.factories.auth_ticket import AuthTicket
from tests.common.factories.authz_code import AuthzCode
from tests.common.factories.base import set_session
from tests.common.factories.document import Document, DocumentMeta, DocumentURI
from tests.common.factories.feature import Feature
from tests.common.factories.feature_cohort import FeatureCohort
from tests.common.factories.flag import Flag
from tests.common.factories.group import Group, OpenGroup, RestrictedGroup
from tests.common.factories.group_scope import GroupScope
from tests.common.factories.job import ExpungeUserJob, Job, SyncAnnotationJob
from tests.common.factories.mention import Mention
from tests.common.factories.moderation_log import ModerationLog
from tests.common.factories.organization import Organization
from tests.common.factories.setting import Setting
from tests.common.factories.subscriptions import Subscriptions
from tests.common.factories.task_done import TaskDone
from tests.common.factories.token import DeveloperToken, OAuth2Token
from tests.common.factories.user import User
from tests.common.factories.user_deletion import UserDeletion
from tests.common.factories.user_identity import UserIdentity
