from django.utils.html import escapejs
from django.utils.translation import ugettext as _

from freenasUI.api.resources import (
    CronJobResourceMixin, RsyncResourceMixin, SMARTTestResourceMixin
)
from freenasUI.freeadmin.options import BaseFreeAdmin
from freenasUI.freeadmin.site import site
from freenasUI.tasks import models

human_colums = [
    {
        'name': 'human_minute',
        'label': _('Minute'),
        'sortable': False,
    },
    {
        'name': 'human_hour',
        'label': _('Hour'),
        'sortable': False,
    },
    {
        'name': 'human_daymonth',
        'label': _('Day of month'),
        'sortable': False,
    },
    {
        'name': 'human_month',
        'label': _('Month'),
        'sortable': False,
    },
    {
        'name': 'human_dayweek',
        'label': _('Day of week'),
        'sortable': False,
    },
]


class CronJobFAdmin(BaseFreeAdmin):

    icon_model = u"cronJobIcon"
    icon_object = u"cronJobIcon"
    icon_add = u"AddcronJobIcon"
    icon_view = u"ViewcronJobIcon"
    exclude_fields = (
        'id',
        'cron_daymonth',
        'cron_dayweek',
        'cron_hour',
        'cron_minute',
        'cron_month',
    )
    menu_child_of = 'tasks'
    resource_mixin = CronJobResourceMixin

    def get_actions(self):
        actions = super(CronJobFAdmin, self).get_actions()
        actions['RunNow'] = {
            'button_name': _('Run Now'),
            'on_click': """function() {
                var mybtn = this;
                for (var i in grid.selection) {
                    var data = grid.row(i).data;
                    editObject('%s', data._run_url, [mybtn,]);
                }
            }""" % (escapejs(_('Run Now')), ),
        }
        return actions

    def get_datagrid_columns(self):
        columns = super(CronJobFAdmin, self).get_datagrid_columns()
        for idx, column in enumerate(human_colums):
            columns.insert(3 + idx, dict(column))
        return columns


class RsyncFAdmin(BaseFreeAdmin):

    icon_model = u"rsyncIcon"
    icon_object = u"rsyncIcon"
    icon_add = u"AddrsyncTaskIcon"
    icon_view = u"ViewrsyncTaskIcon"
    exclude_fields = (
        'id',
        'rsync_mode',
        'rsync_daymonth',
        'rsync_dayweek',
        'rsync_hour',
        'rsync_minute',
        'rsync_month',
        'rsync_recursive',
        'rsync_times',
        'rsync_compress',
        'rsync_archive',
        'rsync_delete',
        'rsync_quiet',
        'rsync_preserveperm',
        'rsync_preserveattr',
        'rsync_extra',
    )
    menu_child_of = 'tasks'
    resource_mixin = RsyncResourceMixin

    def get_actions(self):
        actions = super(RsyncFAdmin, self).get_actions()
        actions['RunNow'] = {
            'button_name': _('Run Now'),
            'on_click': """function() {
                var mybtn = this;
                for (var i in grid.selection) {
                    var data = grid.row(i).data;
                    editObject('%s', data._run_url, [mybtn,]);
                }
            }""" % (escapejs(_('Run Now')), ),
        }
        return actions

    def get_datagrid_columns(self):
        columns = super(RsyncFAdmin, self).get_datagrid_columns()
        for idx, column in enumerate(human_colums):
            columns.insert(6 + idx, dict(column))
        return columns


class SMARTTestFAdmin(BaseFreeAdmin):

    icon_model = u"SMARTIcon"
    icon_object = u"SMARTIcon"
    icon_add = u"AddSMARTTestIcon"
    icon_view = u"ViewSMARTTestIcon"
    exclude_fields = (
        'id',
        'smarttest_daymonth',
        'smarttest_dayweek',
        'smarttest_hour',
        'smarttest_month',
    )
    menu_child_of = 'tasks'
    resource_mixin = SMARTTestResourceMixin

    def get_datagrid_columns(self):
        columns = super(SMARTTestFAdmin, self).get_datagrid_columns()
        for idx, column in enumerate(human_colums[1:]):
            columns.insert(3 + idx, dict(column))
        return columns

site.register(models.CronJob, CronJobFAdmin)
site.register(models.Rsync, RsyncFAdmin)
site.register(models.SMARTTest, SMARTTestFAdmin)
