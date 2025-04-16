# Chat Page for AI Trading Assistant
# This module implements the chat interface for direct communication with the AI bot

import dash
from dash import dcc, html, callback
from dash.dependencies import Input, Output, State
import dash_uploader as du
import base64
import os
import sys
from datetime import datetime
import json
import uuid

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import project modules
from ai_integration.gemini_integration_manager import gemini_manager
from ai_integration.media_processor import MediaProcessor

# Initialize media processor
media_processor = MediaProcessor()

def get_chat_page_layout():
    """Get the layout for the chat page."""
    return html.Div([
        html.H1("Chat with AI Assistant", className="dashboard-title"),
        
        # Chat container with messages
        html.Div([
            html.Div(id="chat-messages-container", className="chat-messages-container"),
        ], className="chat-container"),
        
        # Input area
        html.Div([
            # File upload area
            html.Div([
                dcc.Upload(
                    id='chat-upload',
                    children=html.Div([
                        html.I(className="fas fa-paperclip"),
                        html.Span(" Attach", className="upload-text")
                    ]),
                    className="chat-upload-button",
                    multiple=False
                ),
                html.Div(id="upload-status", className="upload-status")
            ], className="chat-upload-container"),
            
            # Text input and send button
            html.Div([
                dcc.Textarea(
                    id="chat-input",
                    placeholder="Type your message here...",
                    className="chat-input",
                    rows=2
                ),
                html.Button(
                    html.I(className="fas fa-paper-plane"),
                    id="send-button",
                    className="send-button",
                    **{'aria-label': 'Send message'}
                )
            ], className="chat-input-container")
        ], className="chat-controls"),
        
        # Clear chat button
        html.Button(
            "Clear Chat",
            id="clear-chat-button",
            className="clear-chat-button"
        ),
        
        # Store for chat history
        dcc.Store(id="chat-history-store"),
        
        # Store for uploaded files
        dcc.Store(id="uploaded-files-store")
    ], className="chat-page-container")

def register_chat_callbacks(app):
    """Register callbacks for the chat page."""
    
    # Callback to handle file uploads
    @app.callback(
        [
            Output("upload-status", "children"),
            Output("uploaded-files-store", "data")
        ],
        [Input("chat-upload", "contents")],
        [State("chat-upload", "filename"),
         State("uploaded-files-store", "data")]
    )
    def handle_upload(contents, filename, current_uploads):
        if contents is None:
            return "", current_uploads or {}
        
        # Initialize uploads store if needed
        if current_uploads is None:
            current_uploads = {}
        
        try:
            # Get content type and data
            content_type, content_string = contents.split(',', 1)
            
            # Generate a unique ID for this upload
            file_id = str(uuid.uuid4())
            
            # Save file info to store
            current_uploads[file_id] = {
                "filename": filename,
                "content_type": content_type,
                "data": content_string,  # Base64 encoded data
                "timestamp": datetime.now().isoformat()
            }
            
            return html.Div([
                html.I(className="fas fa-check"),
                f" {filename} ready to send"
            ], className="upload-success"), current_uploads
            
        except Exception as e:
            return html.Div([
                html.I(className="fas fa-exclamation-triangle"),
                f" Error: {str(e)}"
            ], className="upload-error"), current_uploads
    
    # Callback to send message and get response
    @app.callback(
        [
            Output("chat-messages-container", "children"),
            Output("chat-input", "value"),
            Output("chat-history-store", "data"),
            Output("uploaded-files-store", "data", allow_duplicate=True)
        ],
        [
            Input("send-button", "n_clicks")
        ],
        [
            State("chat-input", "value"),
            State("chat-history-store", "data"),
            State("uploaded-files-store", "data")
        ],
        prevent_initial_call=True
    )
    def send_message(n_clicks, message, chat_history, uploaded_files):
        if n_clicks is None or (not message and not uploaded_files):
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        # Initialize chat history if needed
        if chat_history is None:
            chat_history = []
        
        # Get user ID (using default for non-auth version)
        user_id = 'default'
        
        # Get Gemini integration
        gemini = gemini_manager.get_integration(user_id)
        
        # Process message and any uploads
        has_media = uploaded_files and len(uploaded_files) > 0
        
        # Add user message to chat history
        timestamp = datetime.now().isoformat()
        user_message = {
            "sender": "user",
            "text": message or "",
            "has_media": has_media,
            "media": uploaded_files if has_media else None,
            "timestamp": timestamp
        }
        chat_history.append(user_message)
        
        # Generate AI response
        try:
            # Prepare prompt with context from chat history
            context = "\n".join([f"{'User' if msg['sender'] == 'user' else 'AI'}: {msg['text']}" 
                               for msg in chat_history[-5:] if msg['text']])
            
            # Handle media if present
            if has_media:
                # For simplicity, we'll just use the first uploaded file
                file_id = list(uploaded_files.keys())[0]
                file_info = uploaded_files[file_id]
                
                # Process based on content type
                if "image" in file_info["content_type"]:
                    # Save base64 image to temp file for processing
                    temp_dir = os.path.join(os.path.dirname(__file__), "../../data/temp")
                    os.makedirs(temp_dir, exist_ok=True)
                    temp_file = os.path.join(temp_dir, file_info["filename"])
                    
                    with open(temp_file, "wb") as f:
                        f.write(base64.b64decode(file_info["data"]))
                    
                    # Analyze image
                    prompt = message or "Analyze this image in the context of trading and finance."
                    response_data = gemini.analyze_image(temp_file, prompt)
                    
                    # Clean up temp file
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                else:
                    # Text-only response for non-image uploads
                    prompt = f"User uploaded a file named {file_info['filename']}. " + (message or "")
                    response_data = gemini.analyze_text(prompt, context)
            else:
                # Text-only message
                response_data = gemini.analyze_text(message, context)
            
            # Extract response text
            if "error" in response_data:
                ai_text = f"Error: {response_data['error']}"
            else:
                # Extract text from Gemini response
                try:
                    ai_text = response_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    if not ai_text:
                        ai_text = "I'm sorry, I couldn't generate a response. Please try again."
                except (KeyError, IndexError):
                    ai_text = "I'm sorry, I couldn't generate a response. Please try again."
        except Exception as e:
            ai_text = f"Error: {str(e)}"
        
        # Add AI response to chat history
        ai_message = {
            "sender": "ai",
            "text": ai_text,
            "has_media": False,  # For now, AI doesn't send media
            "timestamp": datetime.now().isoformat()
        }
        chat_history.append(ai_message)
        
        # Render chat messages
        chat_messages = []
        for msg in chat_history:
            if msg["sender"] == "user":
                # User message
                message_content = []
                
                # Add text if present
                if msg["text"]:
                    message_content.append(html.P(msg["text"]))
                
                # Add media preview if present
                if msg["has_media"] and msg["media"]:
                    for file_id, file_info in msg["media"].items():
                        if "image" in file_info["content_type"]:
                            message_content.append(html.Img(
                                src=f"data:{file_info['content_type']},{file_info['data']}",
                                className="chat-image"
                            ))
                        else:
                            message_content.append(html.Div([
                                html.I(className="fas fa-file"),
                                f" {file_info['filename']}"
                            ], className="chat-file"))
                
                chat_messages.append(html.Div(
                    message_content,
                    className="chat-message user-message"
                ))
            else:
                # AI message
                chat_messages.append(html.Div(
                    html.P(msg["text"]),
                    className="chat-message ai-message"
                ))
        
        # Clear uploaded files after sending
        return chat_messages, "", chat_history, {}

    # Callback to clear chat history
    @app.callback(
        [
            Output("chat-messages-container", "children", allow_duplicate=True),
            Output("chat-history-store", "data", allow_duplicate=True)
        ],
        [Input("clear-chat-button", "n_clicks")],
        prevent_initial_call=True
    )
    def clear_chat(n_clicks):
        if n_clicks:
            return [], []
        return dash.no_update, dash.no_update