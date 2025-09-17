"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2024-01-15 10:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("is_superuser", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    # Create mcp_projects table
    op.create_table(
        "mcp_projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("python_version", sa.String(length=10), nullable=True),
        sa.Column("tools", sa.JSON(), nullable=True),
        sa.Column("requirements", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "CREATED",
                "BUILDING",
                "BUILD_FAILED",
                "BUILT",
                "DEPLOYED",
                "DEPLOY_FAILED",
                name="projectstatusenum",
            ),
            nullable=True,
        ),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_mcp_projects_id"), "mcp_projects", ["id"], unique=False)
    op.create_index(
        op.f("ix_mcp_projects_name"), "mcp_projects", ["name"], unique=False
    )

    # Create mcp_servers table
    op.create_table(
        "mcp_servers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("server_type", sa.String(length=50), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column(
            "transport",
            sa.Enum("STDIO", "SSE", "WEBSOCKET", name="transporttypeenum"),
            nullable=True,
        ),
        sa.Column("tools", sa.JSON(), nullable=True),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("CONNECTED", "DISCONNECTED", "ERROR", name="serverstatusenum"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_mcp_servers_id"), "mcp_servers", ["id"], unique=False)
    op.create_index(op.f("ix_mcp_servers_name"), "mcp_servers", ["name"], unique=True)

    # Create llm_clients table
    op.create_table(
        "llm_clients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("client_type", sa.String(length=50), nullable=False),
        sa.Column("endpoint", sa.String(length=500), nullable=True),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_llm_clients_id"), "llm_clients", ["id"], unique=False)
    op.create_index(op.f("ix_llm_clients_name"), "llm_clients", ["name"], unique=True)

    # Create secrets table
    op.create_table(
        "secrets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("encrypted_value", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("used_by", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index(op.f("ix_secrets_id"), "secrets", ["id"], unique=False)
    op.create_index(op.f("ix_secrets_key"), "secrets", ["key"], unique=True)

    # Create user_sessions table
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("session_token", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_token"),
    )
    op.create_index(op.f("ix_user_sessions_id"), "user_sessions", ["id"], unique=False)
    op.create_index(
        op.f("ix_user_sessions_session_token"),
        "user_sessions",
        ["session_token"],
        unique=True,
    )

    # Create build_history table
    op.create_table(
        "build_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("build_id", sa.String(length=100), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("logs", sa.JSON(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["mcp_projects.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("build_id"),
    )
    op.create_index(
        op.f("ix_build_history_build_id"), "build_history", ["build_id"], unique=True
    )
    op.create_index(op.f("ix_build_history_id"), "build_history", ["id"], unique=False)

    # Create client_connections table
    op.create_table(
        "client_connections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("server_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["client_id"],
            ["llm_clients.id"],
        ),
        sa.ForeignKeyConstraint(
            ["server_id"],
            ["mcp_servers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_client_connections_id"), "client_connections", ["id"], unique=False
    )

    # Create tool_permissions table
    op.create_table(
        "tool_permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tool_name", sa.String(length=100), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("server_id", sa.Integer(), nullable=False),
        sa.Column(
            "permission",
            sa.Enum("ALLOWED", "DENIED", "PENDING", name="permissionstatusenum"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["client_id"],
            ["llm_clients.id"],
        ),
        sa.ForeignKeyConstraint(
            ["server_id"],
            ["mcp_servers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tool_permissions_id"), "tool_permissions", ["id"], unique=False
    )

    # Create audit_logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=50), nullable=False),
        sa.Column("resource_id", sa.String(length=100), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_id"), "audit_logs", ["id"], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f("ix_audit_logs_id"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index(op.f("ix_tool_permissions_id"), table_name="tool_permissions")
    op.drop_table("tool_permissions")

    op.drop_index(op.f("ix_client_connections_id"), table_name="client_connections")
    op.drop_table("client_connections")

    op.drop_index(op.f("ix_build_history_id"), table_name="build_history")
    op.drop_index(op.f("ix_build_history_build_id"), table_name="build_history")
    op.drop_table("build_history")

    op.drop_index(op.f("ix_user_sessions_session_token"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_id"), table_name="user_sessions")
    op.drop_table("user_sessions")

    op.drop_index(op.f("ix_secrets_key"), table_name="secrets")
    op.drop_index(op.f("ix_secrets_id"), table_name="secrets")
    op.drop_table("secrets")

    op.drop_index(op.f("ix_llm_clients_name"), table_name="llm_clients")
    op.drop_index(op.f("ix_llm_clients_id"), table_name="llm_clients")
    op.drop_table("llm_clients")

    op.drop_index(op.f("ix_mcp_servers_name"), table_name="mcp_servers")
    op.drop_index(op.f("ix_mcp_servers_id"), table_name="mcp_servers")
    op.drop_table("mcp_servers")

    op.drop_index(op.f("ix_mcp_projects_name"), table_name="mcp_projects")
    op.drop_index(op.f("ix_mcp_projects_id"), table_name="mcp_projects")
    op.drop_table("mcp_projects")

    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS permissionstatusenum")
    op.execute("DROP TYPE IF EXISTS serverstatusenum")
    op.execute("DROP TYPE IF EXISTS transporttypeenum")
    op.execute("DROP TYPE IF EXISTS projectstatusenum")
