# Copyright 2025 BMO Soluciones, S.A.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""User CRUD routes."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from coati_payroll.auth import proteger_passwd
from coati_payroll.forms import UserForm
from coati_payroll.i18n import _
from coati_payroll.model import Usuario, db
from coati_payroll.vistas.constants import PER_PAGE

user_bp = Blueprint("user", __name__, url_prefix="/user")


@user_bp.route("/")
@login_required
def index():
    """List all users with pagination."""
    page = request.args.get("page", 1, type=int)
    pagination = db.paginate(
        db.select(Usuario).order_by(Usuario.usuario),
        page=page,
        per_page=PER_PAGE,
        error_out=False,
    )
    return render_template(
        "modules/user/index.html", users=pagination.items, pagination=pagination
    )


@user_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    """Create a new user."""
    form = UserForm()

    if form.validate_on_submit():
        user = Usuario()
        user.usuario = form.usuario.data
        if form.password.data:
            user.acceso = proteger_passwd(form.password.data)
        else:
            flash(_("La contraseña es requerida para nuevos usuarios."), "error")
            return render_template(
                "modules/user/form.html", form=form, title=_("Nuevo Usuario")
            )

        user.nombre = form.nombre.data
        user.apellido = form.apellido.data
        user.correo_electronico = form.correo_electronico.data
        user.tipo = form.tipo.data
        user.activo = form.activo.data
        user.creado_por = current_user.usuario

        db.session.add(user)
        db.session.commit()
        flash(_("Usuario creado exitosamente."), "success")
        return redirect(url_for("user.index"))

    return render_template(
        "modules/user/form.html", form=form, title=_("Nuevo Usuario")
    )


@user_bp.route("/edit/<string:id>", methods=["GET", "POST"])
@login_required
def edit(id: str):
    """Edit an existing user."""
    user = db.session.get(Usuario, id)
    if not user:
        flash(_("Usuario no encontrado."), "error")
        return redirect(url_for("user.index"))

    form = UserForm(obj=user)

    if form.validate_on_submit():
        user.usuario = form.usuario.data
        if form.password.data:
            user.acceso = proteger_passwd(form.password.data)
        user.nombre = form.nombre.data
        user.apellido = form.apellido.data
        user.correo_electronico = form.correo_electronico.data
        user.tipo = form.tipo.data
        user.activo = form.activo.data
        user.modificado_por = current_user.usuario

        db.session.commit()
        flash(_("Usuario actualizado exitosamente."), "success")
        return redirect(url_for("user.index"))

    # Don't show password in form
    form.password.data = ""
    return render_template(
        "modules/user/form.html", form=form, title=_("Editar Usuario"), user=user
    )


@user_bp.route("/delete/<string:id>", methods=["POST"])
@login_required
def delete(id: str):
    """Delete a user."""
    user = db.session.get(Usuario, id)
    if not user:
        flash(_("Usuario no encontrado."), "error")
        return redirect(url_for("user.index"))

    if user.id == current_user.id:
        flash(_("No puedes eliminar tu propio usuario."), "error")
        return redirect(url_for("user.index"))

    db.session.delete(user)
    db.session.commit()
    flash(_("Usuario eliminado exitosamente."), "success")
    return redirect(url_for("user.index"))
