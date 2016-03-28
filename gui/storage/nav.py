from freenasUI.freeadmin.tree import TreeNode
from django.utils.translation import ugettext_lazy as _
import models

NAME = _('Storage')
BLACKLIST = ['Disk', 'ReplRemote', 'Volume']
ICON = u'StorageIcon'
ORDER = 20


class ViewRemote(TreeNode):

    gname = 'View'
    type = 'openstorage'
    append_to = 'storage.Replication'


class ViewPeriodic(TreeNode):

    gname = 'View'
    type = 'openstorage'
    append_to = 'storage.Task'


class ViewScrub(TreeNode):

    gname = 'View'
    type = 'openstorage'
    append_to = 'storage.Scrub'


class ViewSnap(TreeNode):

    gname = 'Snapshots.View'
    name = _(u'Snapshots')
    type = 'openstorage'
    icon = u'ViewAllPeriodicSnapIcon'


class ViewVMWare(TreeNode):

    gname = 'View'
    type = 'openstorage'
    append_to = 'storage.VMWarePlugin'


class AddVolume(TreeNode):

    gname = 'Add'
    name = _(u'Volume Manager')
    view = 'storage_volumemanager'
    type = 'volumewizard'
    icon = u'AddVolumeIcon'
    app_name = 'storage'
    model = 'Volumes'
    skip = True
    order = -20


class ImportDisk(TreeNode):

    gname = 'Import'
    name = _(u'Import Disk')
    view = 'storage_import'
    type = 'volumewizard'
    icon = u'ImportVolumeIcon'
    app_name = 'storage'
    model = 'Volume'
    skip = True


class ViewDisks(TreeNode):

    gname = 'ViewDisks'
    name = _(u'View Disks')
    view = 'freeadmin_storage_disk_datagrid'
    type = 'view'
    icon = u'ViewAllVolumesIcon'
    app_name = 'storage'
    model = 'Disk'
    skip = True


class ViewMultipaths(TreeNode):

    gname = 'storage.View.Multipaths'
    name = _(u'View Multipaths')
    view = 'storage_multipath_status'
    type = 'view'
    icon = u'ViewAllVolumesIcon'
    app_name = 'storage'
    model = 'Disk'
    skip = True


class ImportVolume(TreeNode):

    gname = 'ImportVolume'
    name = _(u'Import Volume')
    view = 'storage_autoimport'
    type = 'volumewizard'
    icon = u'ImportVolumeIcon'
    app_name = 'storage'
    model = 'Volume'
    skip = True


class ViewVolumes(TreeNode):

    gname = 'View'
    name = _(u'View Volumes')
    view = u'storage_home'
    type = 'openstorage'
    icon = u'ViewAllVolumesIcon'
    app_name = 'storage'
    model = 'Volumes'
    skip = True


class AddZVol(TreeNode):

    gname = 'storage.ZVol.Add'
    name = _(u'Create zvol')
    view = 'storage_zvol'
    icon = u'AddZFSVolumeIcon'
    type = 'object'
    app_name = 'storage'
    model = 'Volumes'
    skip = True


class CreatePeriodicSnap(TreeNode):

    gname = 'Add'
    name = _(u'Add Periodic Snapshot')
    view = 'freeadmin_storage_task_add'
    icon = u'CreatePeriodicSnapIcon'
    type = 'object'
    app_name = 'storage'
    model = 'Task'
    append_to = 'storage.Task'


class Volumes(TreeNode):

    gname = 'Volumes'
    name = _(u'Volumes')
    icon = u'VolumesIcon'
    order = -1

    def _gen_dataset(self, node, dataset):
        if dataset.name.startswith('.'):
            return

        nav = TreeNode(dataset.name)
        nav.name = dataset.mountpoint
        nav.icon = u'VolumesIcon'

        ds = TreeNode('Dataset')
        ds.name = _(u'Create Dataset')
        ds.view = 'storage_dataset'
        ds.icon = u'AddDatasetIcon'
        ds.type = 'object'
        ds.kwargs = {'fs': dataset.path}
        nav.append_child(ds)

        subnav = TreeNode('ChangePermissions')
        subnav.name = _(u'Change Permissions')
        subnav.type = 'editobject'
        subnav.view = 'storage_mp_permission'
        subnav.kwargs = {'path': dataset.mountpoint}
        subnav.model = 'Volumes'
        subnav.icon = u'ChangePasswordIcon'
        subnav.app_name = 'storage'

        zv = AddZVol()
        zv.kwargs = {'parent': dataset.path}

        node.append_child(nav)
        nav.append_child(subnav)
        nav.append_child(zv)
        for child in dataset.children:
            self._gen_dataset(nav, child)

    def __init__(self, *args, **kwargs):

        super(Volumes, self).__init__(*args, **kwargs)
        self.append_children([
            AddVolume(),
            ImportDisk(),
            ImportVolume(),
            ViewVolumes(),
            ViewDisks(),
        ])

        has_multipath = models.Disk.objects.exclude(
            disk_multipath_name=''
        ).exists()
        if has_multipath:
            self.append_child(ViewMultipaths())

        for i in models.Volume.objects.order_by('-id'):
            nav = TreeNode(i.id)
            nav.name = i.vol_path
            nav.order = -i.id
            nav.model = 'Volume'
            nav.kwargs = {'oid': i.id, 'model': 'Volume'}
            nav.icon = u'VolumesIcon'

            if i.vol_fstype == 'ZFS':
                ds = TreeNode('Dataset')
                ds.name = _(u'Create Dataset')
                ds.view = 'storage_dataset'
                ds.icon = u'AddDatasetIcon'
                ds.type = 'object'
                ds.kwargs = {'fs': i.vol_name}
                nav.append_child(ds)

                zv = AddZVol()
                zv.kwargs = {'parent': i.vol_name}
                nav.append_child(zv)

            subnav = TreeNode('ChangePermissions')
            subnav.name = _('Change Permissions')
            subnav.type = 'editobject'
            subnav.view = 'storage_mp_permission'
            subnav.kwargs = {'path': i.vol_path}
            subnav.model = 'Volume'
            subnav.icon = u'ChangePasswordIcon'
            subnav.app_name = 'storage'

            datasets = i.get_datasets(hierarchical=True)
            if datasets:
                for name, d in datasets.items():
                    # TODO: non-recursive algo
                    self._gen_dataset(nav, d)

            nav.append_child(subnav)
            self.insert_child(0, nav)
