# -----------------------------------------------------------------------
# OpenXenManager
#
# Copyright (C) 2009 Alberto Gonzalez Rodriguez alberto@pesadilla.org
# Copyright (C) 2014 Daniel Lintott <daniel@serverb.co.uk>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# -----------------------------------------------------------------------
from os import path
import utils
import gtk


class oxcWindowAlerts:
    """
    Class used to manage window alerts
    """
    def on_btclosewindowalerts_clicked(self, widget, data=None):
        """
        Function called when "close" button on window alerts is pressed
        """
        self.builder.get_object("windowalerts").hide()

    def on_btalertdismissall_clicked(self, widget, data=None):
        """
        Function called when "Dismiss All" button on window alerts is pressed
        """
        # Show a dialog asking confirmation
        self.builder.get_object("dialogdismissall").run()

    def on_btalertdismiss_clicked(self, widget, data=None):
        """
        Function called when presses "Dismiss" button  on windows alerts
        """
        # Get selected alert
        selection = self.treealerts.get_selection()
        if selection.get_selected()[1] != None:
            iter = selection.get_selected()[1]
            ref = self.listalerts.get_value(iter, 4)
            host = self.listalerts.get_value(iter, 5)
            # Remove from server, if returns "0", alert was removed
            if self.xc_servers[host].dismiss_alert(ref) == 0:
                # Delete from list
                self.listalerts.remove(iter)
                # And update alerts
                self.update_n_alerts()

    def on_dialogdismissall_response(self, dialog, response):
        """
        Callback for the response from Dismiss all confirmation dialog
        """
        dialog.hide()
        if response == gtk.RESPONSE_YES:
            # Response Yes
            self.listalerts.foreach(self.dismiss_all, "")
            # Clear list
            self.builder.get_object("listalerts").clear()
            # Update number of alerts
            self.update_n_alerts()

    def dismiss_all(self, model, path, iter, user_data):
        # Remove alert from list
        listalerts = self.builder.get_object("listalerts")
        self.xc_servers[self.selected_host].dismiss_alert(listalerts.get_value(iter, 4))
        #self.listalerts.remove(iter)

    def update_n_alerts(self):
        """
        Function called to update number of alerts
        """
        self.nelements = 0
        self.listalerts.foreach(self.count_list, self.nelements)
        self.builder.get_object("lblnalerts").set_text("System Alerts: " + str(self.nelements/2))
        if self.nelements:
            self.builder.get_object("imagealerts").set_from_file(path.join(utils.module_path(), "images/alert.png"))
            self.builder.get_object("lbltbalerts").set_markup("<span foreground='red'><b>  System Alerts: " +
                                                              str(self.nelements/2) + "</b></span>")
        else:
            self.builder.get_object("imagealerts").set_from_file(path.join(utils.module_path(), "images/ok.png"))
            self.builder.get_object("lbltbalerts").set_markup("  No System Alerts: ")
