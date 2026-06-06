import streamlit as st
import re
from datetime import datetime
import io

def parse_meeting_notes(raw_text):
    """Parse raw meeting notes into structured sections."""
    lines = raw_text.strip().split('\n')
    
    # Initialize sections
    sections = {
        'summary': [],
        'action_items': [],
        'decisions': [],
        'follow_ups': [],
        'attendees': [],
        'date': datetime.now().strftime('%Y-%m-%d')
    }
    
    # Extract date if present
    date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
    for line in lines[:5]:
        match = re.search(date_pattern, line)
        if match:
            sections['date'] = match.group(1)
            break
    
    # Extract attendees
    attendee_patterns = [
        r'attendees?:?\s*(.+?)(?:\n|$)',
        r'present:?\s*(.+?)(?:\n|$)',
        r'attendance:?\s*(.+?)(?:\n|$)'
    ]
    for pattern in attendee_patterns:
        for line in lines:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                attendees = [a.strip() for a in match.group(1).split(',')]
                sections['attendees'].extend(attendees)
                break
    
    # Categorize lines
    current_section = 'summary'
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect section headers
        lower_line = line.lower()
        if re.match(r'^(action items?|to[- ]?dos?|tasks?):', lower_line):
            current_section = 'action_items'
            continue
        elif re.match(r'^(decisions?|agreed?|resolved?):', lower_line):
            current_section = 'decisions'
            continue
        elif re.match(r'^(follow[- ]?ups?|next steps?|pending):', lower_line):
            current_section = 'follow_ups'
            continue
        elif re.match(r'^(summary|overview|notes?):', lower_line):
            current_section = 'summary'
            continue
        
        # Add line to appropriate section
        if current_section == 'action_items':
            # Clean up action items
            line = re.sub(r'^[-*\d.]+', '', line).strip()
            if line and not line.lower().startswith(('action', 'todo', 'task')):
                sections['action_items'].append(line)
        elif current_section == 'decisions':
            line = re.sub(r'^[-*\d.]+', '', line).strip()
            if line and not line.lower().startswith(('decision', 'agree', 'resolve')):
                sections['decisions'].append(line)
        elif current_section == 'follow_ups':
            line = re.sub(r'^[-*\d.]+', '', line).strip()
            if line and not line.lower().startswith(('follow', 'next', 'pending')):
                sections['follow_ups'].append(line)
        else:
            sections['summary'].append(line)
    
    return sections

def format_client_summary(sections):
    """Format parsed sections into a client-ready summary."""
    output = []
    output.append(f"# Meeting Summary - {sections['date']}")
    output.append("")
    
    if sections['attendees']:
        output.append("## Attendees")
        for attendee in sections['attendees']:
            output.append(f"- {attendee}")
        output.append("")
    
    if sections['summary']:
        output.append("## Summary")
        for line in sections['summary']:
            output.append(line)
        output.append("")
    
    if sections['decisions']:
        output.append("## Decisions")
        for i, decision in enumerate(sections['decisions'], 1):
            output.append(f"{i}. {decision}")
        output.append("")
    
    if sections['action_items']:
        output.append("## Action Items")
        for i, item in enumerate(sections['action_items'], 1):
            output.append(f"{i}. [ ] {item}")
        output.append("")
    
    if sections['follow_ups']:
        output.append("## Follow-ups")
        for i, item in enumerate(sections['follow_ups'], 1):
            output.append(f"{i}. {item}")
        output.append("")
    
    return '\n'.join(output)

def main():
    st.set_page_config(
        page_title="Meeting Notes Formatter",
        page_icon="📝",
        layout="centered"
    )
    
    st.title("📝 Meeting Notes Formatter")
    st.markdown("""
    Transform your raw meeting notes into a structured, client-ready summary.
    Just paste or upload your notes below.
    """)
    
    # Input method selection
    input_method = st.radio(
        "Choose input method:",
        ["Paste text", "Upload file"],
        horizontal=True
    )
    
    raw_text = ""
    
    if input_method == "Paste text":
        raw_text = st.text_area(
            "Paste your meeting notes here:",
            height=200,
            placeholder="Enter your raw meeting notes...\n\nTip: Include sections like 'Action Items:', 'Decisions:', 'Follow-ups:' for better parsing."
        )
    else:
        uploaded_file = st.file_uploader(
            "Upload a text file (.txt, .md)",
            type=['txt', 'md'],
            help="Upload your meeting notes as a text file"
        )
        if uploaded_file:
            try:
                raw_text = uploaded_file.read().decode('utf-8')
                st.success(f"File '{uploaded_file.name}' uploaded successfully!")
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
                return
    
    if st.button("Format Notes", type="primary", disabled=not raw_text.strip()):
        if not raw_text.strip():
            st.warning("Please enter or upload some meeting notes first.")
            return
        
        try:
            with st.spinner("Formatting your meeting notes..."):
                sections = parse_meeting_notes(raw_text)
                formatted_summary = format_client_summary(sections)
            
            st.success("✅ Notes formatted successfully!")
            
            # Display results
            st.subheader("📋 Client-Ready Summary")
            st.markdown(formatted_summary)
            
            # Download button
            buf = io.BytesIO()
            buf.write(formatted_summary.encode('utf-8'))
            buf.seek(0)
            
            st.download_button(
                label="📥 Download Summary",
                data=buf,
                file_name=f"meeting_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                help="Download the formatted summary as a Markdown file"
            )
            
        except Exception as e:
            st.error(f"An error occurred while formatting: {str(e)}")
            st.info("Please check your input and try again. Make sure the text is properly formatted.")
    
    # Help section
    with st.expander("ℹ️ Tips for best results"):
        st.markdown("""
        - **Section headers**: Use clear headers like `Action Items:`, `Decisions:`, `Follow-ups:`
        - **Attendees**: List attendees at the top with `Attendees:` or `Present:`
        - **Date**: Include a date in common formats (e.g., 2024-01-15, 01/15/2024)
        - **Bullet points**: Use `-` or `*` for lists
        - **Separate sections**: Use blank lines between different sections
        """)

if __name__ == "__main__":
    main()