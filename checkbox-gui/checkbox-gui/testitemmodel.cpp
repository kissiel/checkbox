/*
 * This file is part of Checkbox
 *
 * Copyright 2013 Canonical Ltd.
 *
 * Authors:
 * - Andrew Haigh <andrew.haigh@cellsoftware.co.uk>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; version 3.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "testitemmodel.h"

// Factory class to create or update a TestItem Model
ListModel* TestItemModel::CreateTestListModel(ListModel* model)
{
    // Create a model
    qDebug("TestItemModel::CreateTestListModel()");

    // We can create OR update the model
    if (model==NULL) {
        qDebug("Creating fresh TestItemModel");
        model = new ListModel(new TestItem, qApp);
    } else {
        qDebug("Recreating TestItemModel");
        model->clear();
    }

    // We should interrogate the whitelist here
    const QString engname("");

    GuiEngine* myengine = qApp->findChild<GuiEngine*>(engname);
    if(myengine == NULL) {
        qDebug("Cant find guiengine object");

        // NB: Model will be empty at this point
        return model;
    }

    // Get all of the jobs here
    QList<PBTreeNode*> jobnodes = myengine->GetJobNodes();

    // Need to flatten the tree in the right order here
    JobTreeNode* jt_top = myengine->GetJobTreeNodes();

    if (!jt_top) {
        qDebug("no valid JobTree");
        return NULL;
    }

    QList<JobTreeNode*> flatnodes;

    flatnodes.clear();

    jt_top->Flatten(jt_top,flatnodes);

    // dont forget the "first" node is our internal one
    flatnodes.removeFirst();

    QList<JobTreeNode*>::iterator iter = flatnodes.begin();

    while(iter != flatnodes.end()) {

        PBObjectInterface* iface = NULL;

        JobTreeNode* jnode = *iter;
        if (jnode == NULL) {
            qDebug("We ran out of known nodes!");
            break;
        }

        if (jnode->m_node == NULL) {
            qDebug("must be the top node again");
        }

        PBTreeNode* node = jnode->m_node;
        // is this a valid item for the user?
        QList<QDBusObjectPath> list;

        list.append(node->object_path);

        // check against our filtered list
        QList<QDBusObjectPath> short_valid_list = \
                JobTreeNode::FilteredJobs(list,\
                                       myengine->GetVisibleRunList());

        if (myengine->GetVisibleRunList().count() != 0) {
            // we have _some_ valid tests :)
            if (short_valid_list.isEmpty()) {
                // we dont show this one
                iter++;
                continue;
            }
        }

        double duration;
        QString checksum;
        QString depends;
        QString partial_id;
        QString testname;
        QString requires;
        QString description;
        QString command;
        QString environ;
        QString plugin;
        QString type = tr("Automatic");
        QString user;
        QString via;
        QString group;
        bool check = true; // default to show every test
        QString path;

        QList<QString> parent_names;
        QList<QString> parent_ids;

        // Fill in the parent names
        JobTreeNode* temp = jnode->parent;

        while (temp != jt_top) {
            parent_names.prepend(temp->m_name);

            temp = temp->parent;
        }

        // Fill in the parent ids
        temp = jnode->parent;

        while (temp != jt_top) {
           parent_ids.prepend(temp->m_id);

           temp = temp->parent;
        }

        // The path for this job is:
        path = jnode->m_node->object_path.path();

        for(int j=0; j < node->interfaces.count(); j++) {

            iface = node->interfaces.at(j);

            if (iface == NULL) {
                qDebug("Null interface");
            } else {
                if(iface->interface.compare(PlainboxJobDefinition1) == 0) {
                    QVariant variant;

                    variant = *iface->properties.find("estimated_duration");
                    if (variant.isValid() && variant.canConvert(QMetaType::Double)) {
                        duration = variant.toDouble();
                    }

                    variant = *iface->properties.find("checksum");
                    if (variant.isValid() && variant.canConvert(QMetaType::QString)) {
                        checksum = variant.toString();
                    }

                    variant = *iface->properties.find("depends");
                    if (variant.isValid() && variant.canConvert(QMetaType::QString)) {
                        depends = variant.toString();
                    }
                    variant = *iface->properties.find("description");
                    if (variant.isValid() && variant.canConvert(QMetaType::QString)) {
                        description = variant.toString();
                    }

                    variant = *iface->properties.find("summary");
                    if (variant.isValid() && variant.canConvert(QMetaType::QString) ) {
                        testname = variant.toString();
                    }

                    variant = *iface->properties.find("partial_id");
                    if (variant.isValid() && variant.canConvert(QMetaType::QString) ) {
                        partial_id = variant.toString();
                    }

                    variant = *iface->properties.find("requires");
                    if (variant.isValid() && variant.canConvert(QMetaType::QString)) {
                        requires = variant.toString();
                    }
                }

                if(iface->interface.compare(CheckBoxJobDefinition1) == 0) {
                    QVariant variant;
                    variant = *iface->properties.find("plugin");

                    if (variant.isValid() && variant.canConvert(QMetaType::QString) ) {
                        plugin = variant.toString();

                        /* show plugin type as either Automatic (default) or
                         * Manual.
                         */
                        if (variant.toString().compare("manual") == 0 ||
                                variant.toString().compare("user-interact") == 0 ||
                                variant.toString().compare("user-verify") == 0 ||
                                variant.toString().compare("user-interact-verify") == 0) {
                            type = tr("Manual");
                        }

                        // local jobs should display description if there's no summary
                        // not partial_id
                        if (variant.toString().compare("local") == 0) {
                            if (testname == partial_id) {
                                testname = description;
                            }
                        }
                    }

                    variant = *iface->properties.find("via");
                    if (variant.isValid() && variant.canConvert(QMetaType::QString) ) {
                        via = variant.toString();
                    }

                    variant = *iface->properties.find("command");
                    if (variant.isValid() && variant.canConvert(QMetaType::QString)) {
                        command = variant.toString();
                    }
                }
            }
        }

        // this will signal how far indented this item is
        int depth = 0;
        for (int i=0;i<parent_ids.count();i++) {

            depth++;
        }

        // Does this node have children?
        bool branch = false;
        if (!jnode->m_children.isEmpty()) {
            branch = true;

            /* Avoid trying to determine the Automatic/Manual nature of
             * various categories of tests.
             */
            type = tr("-");
        }

        model->appendRow(
            new TestItem(duration,
                partial_id, checksum, depends, testname, requires, description, command,
                environ, plugin, type, user, group, via, check, path,
                parent_names, parent_ids, depth, branch, model));
        iter++;
    }

    qDebug("TestItemModel::CreateTestListModel() - done");

    return model;
}


QList<QDBusObjectPath> TestItemModel::GetSelectedRealJobs(ListModel* model)
{
    QList<QDBusObjectPath> selected_jobs_list;
    if (!model) {
        qDebug() << "ERROR" << __FUNCTION__ << "model not supplied";
        return selected_jobs_list;
    }
    for (int i=0; i<model->getCount(); i++) {
        QModelIndex index = model->index(i);
        QString objectpath = model->data(
            index, TestItem::ObjectPathRole).toString();
        QString partial_id = model->data(
            index, TestItem::PartialIdRole).toString();
        QString plugin = model->data(
            index, TestItem::PluginRole).toString();
        bool check = model->data(
            index,TestItem::CheckRole).toBool();
        if (check && plugin != "local") {
            qDebug() << "[" << __FUNCTION__ << "]" << " SELECTING " << partial_id;
            QDBusObjectPath opath(objectpath);
            selected_jobs_list.append(opath);
        } else {
            qDebug() << "[" << __FUNCTION__ << "]" << " NOT SELECTING " << partial_id;
        }
    }
    GuiEngine* myengine = qApp->findChild<GuiEngine*>("");
    if (myengine) {
        myengine->SetRealJobsList(selected_jobs_list);
        qDebug() << "[" << __FUNCTION__ << "]" \
            << "SELECTED jobs copied to m_final_run_list";
    } else {
        qDebug() << "ERROR" << __FUNCTION__ << "cannot get gui-engine";
    }
    return selected_jobs_list;
}


QList<QDBusObjectPath> TestItemModel::GetSelectedRerunJobs(ListModel* model)
{
    QList<QDBusObjectPath> selected_rerun_list;
    if (!model) {
        qDebug() << "ERROR" << __FUNCTION__ << "model not supplied";
        return selected_rerun_list;
    }
    for (int i=0; i<model->getCount(); i++) {
        QModelIndex index = model->index(i);
        QString objectpath = model->data(
            index, TestItem::ObjectPathRole).toString();
        QString partial_id = model->data(
            index, TestItem::PartialIdRole).toString();
        QString plugin = model->data(
            index, TestItem::PluginRole).toString();
        bool rerun = model->data(index, TestItem::RerunRole).toBool();
        if (rerun && plugin != "local") {
            qDebug() << "[" << __FUNCTION__ << "]" << "SELECTING" << partial_id;
            selected_rerun_list.append(QDBusObjectPath(objectpath));
        } else {
            qDebug() << "[" << __FUNCTION__ << "]" << "NOT SELECTING" << partial_id;
        }
    }
    GuiEngine* myengine = qApp->findChild<GuiEngine*>("");
    if (myengine) {
        myengine->SetRerunJobsList(selected_rerun_list);
        qDebug() << "[" << __FUNCTION__ << "]" \
            << "SELECTED jobs copied to m_rerun_list";
    } else {
        qDebug() << "ERROR" << __FUNCTION__ << "cannot get gui-engine";
    }
    return selected_rerun_list;
}


/* Track the jobs which are actually needed for display in the runmanager
 * as they will be needed when the gui is reconstructed after a session
 * is resumed
 */
QList<QDBusObjectPath> TestItemModel::GetSelectedVisibleJobs(ListModel* model)
{
    QList<QDBusObjectPath> visible_jobs_list;
    if (!model) {
        qDebug() << "ERROR" << __FUNCTION__ << "model not supplied";
        return visible_jobs_list;
    }
    for (int i=0; i<model->getCount(); i++) {
        QModelIndex index = model->index(i);
        QString objectpath = model->data(
            index, TestItem::ObjectPathRole).toString();
        QString partial_id = model->data(
            index, TestItem::PartialIdRole).toString();
        QString plugin = model->data(
            index, TestItem::PluginRole).toString();
        bool check = model->data(index, TestItem::CheckRole).toBool();
        if (check) {
            qDebug() << "[" << __FUNCTION__ << "]" << "VISIBLE" << partial_id;
            visible_jobs_list.append(QDBusObjectPath(objectpath));
        } else {
            qDebug() << "[" << __FUNCTION__ << "]" << "NOT VISIBLE" << partial_id;
        }
    }
    GuiEngine* myengine = qApp->findChild<GuiEngine*>("");
    if (myengine) {
        myengine->SetVisibleJobsList(visible_jobs_list);
        qDebug() << "[" << __FUNCTION__ << "]" \
            << "VISIBLE jobs copied to m_visible_run_list";
    } else {
        qDebug() << "ERROR" << __FUNCTION__ << "cannot get gui-engine";
    }
    return visible_jobs_list;
}
