#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date  : 2025/6/26 10:00
# @File  : host_agent_api_client.py
# @Author: Johnson Guo
# @Desc  : 使用host agent，调用host agent

import requests
import asyncio
import json
import time
import uuid

class HostAgentAPIClient:
    """
    A client for interacting with the Host Agent API, based on the tests in test_api.py.
    """
    def __init__(self, host='127.0.0.1', port=13000):
        """
        Initializes the API client.
        :param host: host agent的url
        :param port: host agent的端口
        """
        self.host = host
        self.port = port
        self.base_url = f"http://{self.host}:{self.port}"
        self.headers = {'Content-Type': 'application/json'}
        # 检查是否启动
        self.ping()

    def _post_request(self, endpoint, payload=None):
        """
        Helper method to make POST requests.
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return None

    def ping(self):
        """
        Tests the /ping endpoint.
        """
        url = f"{self.base_url}/ping"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return None

    def register_agent(self, agent_url):
        """
        Tests the /agent/register endpoint.
        """
        payload = {"params": agent_url}
        return self._post_request("/agent/register", payload)

    def list_agents(self):
        """
        Tests the /agent/list endpoint.
        """
        return self._post_request("/agent/list")

    def create_conversation(self, conversation_id={}):
        """
        Creates a new conversation.
        """
        payload = {"conversation_id": conversation_id}
        return self._post_request("/conversation/create", payload)
        # if conversation_id:
        #     payload = {"conversation_id": conversation_id}
        #     return self._post_request("/conversation/create", payload)
        # else:
        #     return self._post_request("/conversation/create")

    def list_conversations(self):
        """
        Lists all created conversations.
        """
        return self._post_request("/conversation/list")

    def send_message(self, conversation_id, text, role="user"):
        """
        Sends a message to a conversation.
        """
        message_payload = {
            "params": {
                "role": role,
                "parts": [{"type": "text", "text": text}],
                "messageId": uuid.uuid4().hex,
                "contextId": conversation_id,
            }
        }
        return self._post_request("/message/send", message_payload)

    def list_messages(self, conversation_id):
        """
        Lists messages in a conversation.
        """
        payload = {"params": conversation_id}
        return self._post_request("/message/list", payload)

    def get_pending_messages(self):
        """
        Gets a list of pending messages.
        """
        return self._post_request("/message/pending")

    def get_events(self):
        """
        Gets events.
        """
        return self._post_request("/events/get")

    def query_events(self, conversation_id):
        """
        Queries events for a specific conversation.
        """
        payload = {
            "params": {
                "conversation_id": conversation_id,
            }
        }
        return self._post_request("/events/query", payload)

    def list_tasks(self):
        """
        Lists tasks.
        """
        return self._post_request("/task/list")

    def update_api_key(self, api_key):
        """
        Updates the API key.
        """
        payload = {"api_key": api_key}
        return self._post_request("/api_key/update", payload)

    def send_and_poll_pending(self, conversation_id, text, timeout=120, interval=0.5):
        """
        Sends a message and polls the pending endpoint until the message is processed.
        """
        send_response = self.send_message(conversation_id, text)
        if not send_response or "result" not in send_response:
            print("Failed to send message.")
            return None
        
        message_id = send_response["result"]["message_id"]
        print(f"Message sent, message_id: {message_id}")

        start_time = time.time()
        last_events_number = 0
        while time.time() - start_time < timeout:
            pending_response = self.get_pending_messages()
            if pending_response and "result" in pending_response:
                pending_ids = [item for sublist in pending_response["result"] for item in sublist if item]
                print(f"Pending messages: {pending_ids}")
                if message_id not in pending_ids:
                    print("Message processed.")
                    return True
            events = self.query_events(conversation_id)
            event_results = events["result"]
            new_events = event_results[last_events_number:]
            last_events_number += len(event_results)
            if new_events:
                print(f"有新的事件收到了,事件内容: {new_events}")
            time.sleep(interval)
        
        print(f"Timeout: Message {message_id} still pending after {timeout} seconds.")
        return False

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Host Agent API Client")
    # parser.add_argument("--message", type=str, default="你好。", help="The message to send to the agent.")
    parser.add_argument("--message", type=str, default="帮我研究一个关于依沃西单抗在非小细胞肺癌的临床研究的进展。", help="The message to send to the agent.")
    args = parser.parse_args()

    client = HostAgentAPIClient()
    status = client.register_agent(agent_url="127.0.0.1:10001")
    print(f"Agent注册结果: {status}")
    status = client.register_agent(agent_url="127.0.0.1:10011")
    print(f"Agent注册结果: {status}")

    # 1. Ping the server
    print("Pinging server...")
    pong = client.ping()
    print(f"Server response: {pong}")
    if pong != "Pong":
        print("Server may not be running. Exiting.")
    else:
        # 2. Create a conversation
        print("\n创建会话.")
        conv_response = client.create_conversation()
        if conv_response and conv_response.get("result"):
            conversation_id = conv_response["result"]["conversation_id"]
            print(f"创建会话的id：{conversation_id}")

            # 3. Send a message and wait for it to be processed
            print("\n发送消息，并等待返回结果")
            client.send_and_poll_pending(conversation_id, args.message, timeout=20*60)

            # 4. List messages in the conversation
            print("\n列出已有消息")
            messages = client.list_messages(conversation_id)
            print("Messages in conversation:")
            print(json.dumps(messages, indent=2, ensure_ascii=False))
        else:
            print("Failed to create conversation.")
