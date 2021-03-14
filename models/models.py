from app import db

class OAI_PMH(db.Model):
    __tablename__ = 'OAI_PMH'
    id = db.Column(db.Integer, primary_key=True)
    repository_name = db.Column(db.String(500),  nullable=False)
    url = db.Column(db.String(500),  nullable=False)
    namespace_identifier = db.Column(db.String(150),  nullable=False)
    
    def __init__(self, repository_name, url, namespace_identifier):
        self.repository_name = repository_name
        self.url = url
        self.namespace_identifier = namespace_identifier
        
    def __str__(self):
        return self.repository_name

class ROAR(db.Model):
    __tablename__ = 'ROAR'
    id = db.Column(db.Integer, primary_key=True)
    repository_name = db.Column(db.String(500),  nullable=False)
    home_page = db.Column(db.String(500),  nullable=False)
    oai_pmh = db.Column(db.String(150),  nullable=True)
    
    def __init__(self, repository_name, home_page, oai_pmh):
        self.repository_name = repository_name
        self.home_page = home_page
        self.oai_pmh = oai_pmh
        
    def __str__(self):
        return self.repository_name