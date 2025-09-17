"""Add missing tables for MCP project management

Revision ID: 002
Revises: 001
Create Date: 2024-01-16 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create mcp_templates table
    op.create_table(
        "mcp_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=50), nullable=False),
        sa.Column("framework", sa.String(length=50), nullable=False),
        sa.Column("template_files", sa.JSON(), nullable=True),
        sa.Column("default_config", sa.JSON(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_mcp_templates_id"), "mcp_templates", ["id"], unique=False)
    op.create_index(op.f("ix_mcp_templates_name"), "mcp_templates", ["name"], unique=False)

    # Create project_files table
    op.create_table(
        "project_files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_content", sa.Text(), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["mcp_projects.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_project_files_id"), "project_files", ["id"], unique=False)

    # Create docker_containers table
    op.create_table(
        "docker_containers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("container_id", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("image", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("ports", sa.JSON(), nullable=True),
        sa.Column("environment", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["mcp_projects.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("container_id"),
    )
    op.create_index(op.f("ix_docker_containers_id"), "docker_containers", ["id"], unique=False)
    op.create_index(op.f("ix_docker_containers_container_id"), "docker_containers", ["container_id"], unique=True)

    # Create build_logs table
    op.create_table(
        "build_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("build_id", sa.String(length=100), nullable=False),
        sa.Column("stage", sa.String(length=50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["mcp_projects.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_build_logs_id"), "build_logs", ["id"], unique=False)
    op.create_index(op.f("ix_build_logs_build_id"), "build_logs", ["build_id"], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f("ix_build_logs_build_id"), table_name="build_logs")
    op.drop_index(op.f("ix_build_logs_id"), table_name="build_logs")
    op.drop_table("build_logs")

    op.drop_index(op.f("ix_docker_containers_container_id"), table_name="docker_containers")
    op.drop_index(op.f("ix_docker_containers_id"), table_name="docker_containers")
    op.drop_table("docker_containers")

    op.drop_index(op.f("ix_project_files_id"), table_name="project_files")
    op.drop_table("project_files")

    op.drop_index(op.f("ix_mcp_templates_name"), table_name="mcp_templates")
    op.drop_index(op.f("ix_mcp_templates_id"), table_name="mcp_templates")
    op.drop_table("mcp_templates")