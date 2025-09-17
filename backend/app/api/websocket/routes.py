import logging
from typing import Dict

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.websocket_manager import WebSocketManager, get_websocket_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    ws_manager: WebSocketManager = Depends(get_websocket_manager),
):
    """Main WebSocket endpoint for real-time communication"""
    connection_id = await ws_manager.connect(websocket)
    logger.info(f"WebSocket client connected: {connection_id}")

    try:
        await ws_manager.handle_websocket_communication(websocket, connection_id)
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
    finally:
        ws_manager.disconnect(connection_id)


@router.websocket("/ws/logs/{container_id}")
async def container_logs_websocket(
    websocket: WebSocket,
    container_id: str,
    ws_manager: WebSocketManager = Depends(get_websocket_manager),
):
    """WebSocket endpoint for streaming container logs"""
    connection_id = await ws_manager.connect(websocket)
    logger.info(f"Container logs WebSocket connected: {connection_id} for {container_id}")

    try:
        # Subscribe to container logs channel
        logs_channel = f"container_logs:{container_id}"
        await ws_manager.connection_manager.subscribe_to_channel(connection_id, logs_channel)

        # Start streaming existing logs and new logs
        from app.core.docker_manager import docker_manager
        import asyncio

        async def stream_logs():
            try:
                async for log_line in docker_manager.get_container_logs(
                    container_id, tail=100, follow=True
                ):
                    await ws_manager.connection_manager.send_personal_message(
                        connection_id,
                        {
                            "type": "log",
                            "container_id": container_id,
                            "message": log_line,
                            "timestamp": str(asyncio.get_event_loop().time()),
                        },
                    )
            except Exception as e:
                logger.error(f"Error streaming logs for {container_id}: {e}")
                await ws_manager.connection_manager.send_personal_message(
                    connection_id,
                    {
                        "type": "error",
                        "message": f"Failed to stream logs: {str(e)}",
                    },
                )

        # Start log streaming task
        log_task = asyncio.create_task(stream_logs())

        # Handle WebSocket communication
        await ws_manager.handle_websocket_communication(websocket, connection_id)

    except WebSocketDisconnect:
        logger.info(f"Container logs WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"Container logs WebSocket error: {e}")
    finally:
        # Cancel log streaming task
        if 'log_task' in locals():
            log_task.cancel()
        ws_manager.disconnect(connection_id)


@router.websocket("/ws/builds/{build_id}")
async def build_logs_websocket(
    websocket: WebSocket,
    build_id: str,
    ws_manager: WebSocketManager = Depends(get_websocket_manager),
):
    """WebSocket endpoint for streaming build logs and progress"""
    connection_id = await ws_manager.connect(websocket)
    logger.info(f"Build logs WebSocket connected: {connection_id} for {build_id}")

    try:
        # Subscribe to build events channel
        build_channel = f"build:{build_id}"
        await ws_manager.connection_manager.subscribe_to_channel(connection_id, build_channel)

        # Send current build status
        from app.core.build_manager import build_manager
        build_status = await build_manager.get_build_status(build_id)
        if build_status:
            await ws_manager.connection_manager.send_personal_message(
                connection_id,
                {
                    "type": "build_status",
                    "build_id": build_id,
                    "status": build_status,
                },
            )

        # Handle WebSocket communication
        await ws_manager.handle_websocket_communication(websocket, connection_id)

    except WebSocketDisconnect:
        logger.info(f"Build logs WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"Build logs WebSocket error: {e}")
    finally:
        ws_manager.disconnect(connection_id)


@router.websocket("/ws/system")
async def system_events_websocket(
    websocket: WebSocket,
    ws_manager: WebSocketManager = Depends(get_websocket_manager),
):
    """WebSocket endpoint for system-wide events"""
    connection_id = await ws_manager.connect(websocket)
    logger.info(f"System events WebSocket connected: {connection_id}")

    try:
        # Subscribe to system events channels
        system_channels = [
            "container_events",
            "system_events",
            "health_alerts",
        ]

        for channel in system_channels:
            await ws_manager.connection_manager.subscribe_to_channel(connection_id, channel)

        # Send initial system status
        from app.core.docker_manager import docker_manager
        try:
            system_info = await docker_manager.get_system_info()
            await ws_manager.connection_manager.send_personal_message(
                connection_id,
                {
                    "type": "system_status",
                    "data": system_info,
                },
            )
        except Exception as e:
            logger.warning(f"Could not get system info: {e}")

        # Handle WebSocket communication
        await ws_manager.handle_websocket_communication(websocket, connection_id)

    except WebSocketDisconnect:
        logger.info(f"System events WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"System events WebSocket error: {e}")
    finally:
        ws_manager.disconnect(connection_id)


@router.get("/ws/stats")
async def get_websocket_stats(
    ws_manager: WebSocketManager = Depends(get_websocket_manager),
) -> Dict:
    """Get WebSocket connection statistics"""
    return ws_manager.get_stats()


@router.post("/ws/broadcast")
async def broadcast_message(
    channel: str,
    message: Dict,
    ws_manager: WebSocketManager = Depends(get_websocket_manager),
):
    """Broadcast a message to all subscribers of a channel (admin endpoint)"""
    sent_count = await ws_manager.publish_event(channel, message)
    return {
        "message": "Message broadcasted",
        "channel": channel,
        "recipients": sent_count,
    }