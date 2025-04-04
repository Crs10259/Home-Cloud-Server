from flask import Blueprint, render_template

team = Blueprint('team', __name__)

@team.route('/team')
def index():
    """Display information about the development team"""
    team_members = [
        {
            'name': 'Jane Doe',
            'role': 'Lead Developer',
            'bio': 'Full-stack developer with expertise in Python and JavaScript.',
            'avatar': 'images/team/jane.jpg'
        },
        {
            'name': 'John Smith',
            'role': 'Backend Developer',
            'bio': 'Database expert and API specialist with 5 years of experience.',
            'avatar': 'images/team/john.jpg'
        },
        {
            'name': 'Alex Johnson',
            'role': 'Frontend Developer',
            'bio': 'UI/UX specialist focused on creating beautiful, responsive interfaces.',
            'avatar': 'images/team/alex.jpg'
        },
        {
            'name': 'Sam Williams',
            'role': 'DevOps Engineer',
            'bio': 'Infrastructure and deployment specialist ensuring smooth operations.',
            'avatar': 'images/team/sam.jpg'
        }
    ]
    
    return render_template('team/index.html', team_members=team_members) 