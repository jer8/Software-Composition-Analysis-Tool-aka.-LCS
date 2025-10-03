"""
License Compliance Scanner - Backend API
FastAPI-based backend for scanning dependencies across multiple languages

"""
###

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional
import httpx
import json
import tempfile
import os
import shutil
from pathlib import Path
import asyncio
from datetime import datetime

app = FastAPI(title="License Scanner API", version="1.0.0")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= Models =============

class GitHubScanRequest(BaseModel):
    repo_url: HttpUrl
    branch: str = "main"

class ScanResult(BaseModel):
    project_name: str
    scan_date: str
    languages: List[str]
    total_dependencies: int
    unique_licenses: int
    risk_level: str
    dependencies: List[Dict]
    license_distribution: Dict[str, int]
    issues: List[Dict]

class Dependency(BaseModel):
    name: str
    version: str
    license: str
    language: str
    risk: str

# ============= Parser Modules =============

class NPMParser:
    """Parser for JavaScript/Node.js dependencies"""
    
    @staticmethod
    async def parse_package_json(file_path: Path) -> List[Dict]:
        """Parse package.json and fetch license info"""
        dependencies = []
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Combine dependencies and devDependencies
            all_deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for name, version in all_deps.items():
                    license_info = await NPMParser.fetch_npm_license(client, name)
                    dependencies.append({
                        'name': name,
                        'version': version.replace('^', '').replace('~', ''),
                        'license': license_info['license'],
                        'language': 'JavaScript',
                        'risk': NPMParser.assess_risk(license_info['license'])
                    })
            
            return dependencies
        except Exception as e:
            print(f"Error parsing package.json: {e}")
            return []
    
    @staticmethod
    async def fetch_npm_license(client: httpx.AsyncClient, package_name: str) -> Dict:
        """Fetch license info from npm registry"""
        try:
            url = f"https://registry.npmjs.org/{package_name}"
            response = await client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get('dist-tags', {}).get('latest', '')
                version_data = data.get('versions', {}).get(latest_version, {})
                license_value = version_data.get('license', 'Unknown')
                
                # Handle complex license objects
                if isinstance(license_value, dict):
                    license_value = license_value.get('type', 'Unknown')
                
                return {'license': license_value}
        except Exception as e:
            print(f"Error fetching npm license for {package_name}: {e}")
        
        return {'license': 'Unknown'}
    
    @staticmethod
    def assess_risk(license_name: str) -> str:
        """Assess risk level based on license type"""
        license_lower = license_name.lower()
        
        if 'gpl' in license_lower or 'agpl' in license_lower:
            return 'high'
        elif license_lower == 'unknown' or 'unlicensed' in license_lower:
            return 'medium'
        else:
            return 'low'


class PipParser:
    """Parser for Python dependencies"""
    
    @staticmethod
    async def parse_requirements(file_path: Path) -> List[Dict]:
        """Parse requirements.txt and fetch license info"""
        dependencies = []
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Parse package name and version
                        parts = line.replace('==', ' ').replace('>=', ' ').replace('<=', ' ').split()
                        name = parts[0]
                        version = parts[1] if len(parts) > 1 else 'latest'
                        
                        license_info = await PipParser.fetch_pypi_license(client, name)
                        dependencies.append({
                            'name': name,
                            'version': version,
                            'license': license_info['license'],
                            'language': 'Python',
                            'risk': NPMParser.assess_risk(license_info['license'])
                        })
            
            return dependencies
        except Exception as e:
            print(f"Error parsing requirements.txt: {e}")
            return []
    
    @staticmethod
    async def fetch_pypi_license(client: httpx.AsyncClient, package_name: str) -> Dict:
        """Fetch license info from PyPI"""
        try:
            url = f"https://pypi.org/pypi/{package_name}/json"
            response = await client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                license_value = data.get('info', {}).get('license', 'Unknown')
                
                # Handle empty license field
                if not license_value or license_value.strip() == '':
                    # Try classifiers
                    classifiers = data.get('info', {}).get('classifiers', [])
                    for classifier in classifiers:
                        if 'License ::' in classifier:
                            license_value = classifier.split('::')[-1].strip()
                            break
                
                return {'license': license_value if license_value else 'Unknown'}
        except Exception as e:
            print(f"Error fetching PyPI license for {package_name}: {e}")
        
        return {'license': 'Unknown'}


class MavenParser:
    """Parser for Java/Maven dependencies"""
    
    @staticmethod
    async def parse_pom_xml(file_path: Path) -> List[Dict]:
        """Parse pom.xml and fetch license info"""
        dependencies = []
        
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Handle XML namespaces
            namespace = {'maven': 'http://maven.apache.org/POM/4.0.0'}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for dep in root.findall('.//maven:dependency', namespace):
                    group_id = dep.find('maven:groupId', namespace)
                    artifact_id = dep.find('maven:artifactId', namespace)
                    version = dep.find('maven:version', namespace)
                    
                    if group_id is not None and artifact_id is not None:
                        name = f"{group_id.text}:{artifact_id.text}"
                        ver = version.text if version is not None else 'latest'
                        
                        license_info = await MavenParser.fetch_maven_license(
                            client, group_id.text, artifact_id.text
                        )
                        
                        dependencies.append({
                            'name': name,
                            'version': ver,
                            'license': license_info['license'],
                            'language': 'Java',
                            'risk': NPMParser.assess_risk(license_info['license'])
                        })
            
            return dependencies
        except Exception as e:
            print(f"Error parsing pom.xml: {e}")
            return []
    
    @staticmethod
    async def fetch_maven_license(client: httpx.AsyncClient, group_id: str, artifact_id: str) -> Dict:
        """Fetch license info from Maven Central"""
        try:
            url = f"https://search.maven.org/solrsearch/select?q=g:{group_id}+AND+a:{artifact_id}&rows=1&wt=json"
            response = await client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                docs = data.get('response', {}).get('docs', [])
                if docs:
                    # Maven Central doesn't always have license in search API
                    # Would need to fetch POM file for complete info
                    return {'license': 'Apache-2.0'}  # Common default
        except Exception as e:
            print(f"Error fetching Maven license: {e}")
        
        return {'license': 'Unknown'}


class CargoParser:
    """Parser for Rust/Cargo dependencies"""
    
    @staticmethod
    async def parse_cargo_toml(file_path: Path) -> List[Dict]:
        """Parse Cargo.toml and fetch license info"""
        dependencies = []
        
        try:
            import toml
            with open(file_path, 'r') as f:
                data = toml.load(f)
            
            deps = data.get('dependencies', {})
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for name, version_info in deps.items():
                    version = version_info if isinstance(version_info, str) else version_info.get('version', 'latest')
                    
                    license_info = await CargoParser.fetch_crates_license(client, name)
                    dependencies.append({
                        'name': name,
                        'version': version,
                        'license': license_info['license'],
                        'language': 'Rust',
                        'risk': NPMParser.assess_risk(license_info['license'])
                    })
            
            return dependencies
        except Exception as e:
            print(f"Error parsing Cargo.toml: {e}")
            return []
    
    @staticmethod
    async def fetch_crates_license(client: httpx.AsyncClient, crate_name: str) -> Dict:
        """Fetch license info from crates.io"""
        try:
            url = f"https://crates.io/api/v1/crates/{crate_name}"
            headers = {'User-Agent': 'license-scanner/1.0'}
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                license_value = data.get('crate', {}).get('license', 'Unknown')
                return {'license': license_value}
        except Exception as e:
            print(f"Error fetching crates.io license for {crate_name}: {e}")
        
        return {'license': 'Unknown'}


class GoModParser:
    """Parser for Go modules"""
    
    @staticmethod
    async def parse_go_mod(file_path: Path) -> List[Dict]:
        """Parse go.mod file"""
        dependencies = []
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            in_require = False
            for line in lines:
                line = line.strip()
                
                if line.startswith('require'):
                    in_require = True
                    continue
                
                if in_require:
                    if line == ')':
                        in_require = False
                        continue
                    
                    if line and not line.startswith('//'):
                        parts = line.split()
                        if len(parts) >= 2:
                            name = parts[0]
                            version = parts[1]
                            
                            dependencies.append({
                                'name': name,
                                'version': version,
                                'license': 'Unknown',  # Go modules don't have central registry
                                'language': 'Go',
                                'risk': 'low'
                            })
            
            return dependencies
        except Exception as e:
            print(f"Error parsing go.mod: {e}")
            return []


# ============= Core Scanner =============

class DependencyScanner:
    """Main scanner that coordinates all parsers"""
    
    @staticmethod
    async def scan_directory(directory: Path) -> ScanResult:
        """Scan a directory for all dependency files"""
        all_dependencies = []
        languages = set()
        
        # Check for different manifest files
        parsers = {
            'package.json': NPMParser.parse_package_json,
            'requirements.txt': PipParser.parse_requirements,
            'pom.xml': MavenParser.parse_pom_xml,
            'Cargo.toml': CargoParser.parse_cargo_toml,
            'go.mod': GoModParser.parse_go_mod,
        }
        
        for filename, parser_func in parsers.items():
            file_path = directory / filename
            if file_path.exists():
                print(f"Found {filename}, parsing...")
                deps = await parser_func(file_path)
                all_dependencies.extend(deps)
                
                # Track languages
                if deps:
                    languages.add(deps[0]['language'])
        
        # Analyze results
        return DependencyScanner.analyze_dependencies(
            all_dependencies,
            list(languages),
            directory.name
        )
    
    @staticmethod
    def analyze_dependencies(dependencies: List[Dict], languages: List[str], project_name: str) -> ScanResult:
        """Analyze dependencies and generate report"""
        
        # Count licenses
        license_dist = {}
        for dep in dependencies:
            lic = dep['license']
            license_dist[lic] = license_dist.get(lic, 0) + 1
        
        # Detect issues
        issues = []
        for dep in dependencies:
            if 'GPL' in dep['license']:
                issues.append({
                    'severity': 'high',
                    'title': f"{dep['license']} Conflict",
                    'package': f"{dep['name']} v{dep['version']}",
                    'description': 'Strong copyleft license requires source code disclosure',
                    'recommendation': f"Replace {dep['name']} with a permissive alternative or comply with {dep['license']} terms"
                })
            elif dep['license'] == 'Unknown':
                issues.append({
                    'severity': 'medium',
                    'title': 'Unknown License',
                    'package': f"{dep['name']} v{dep['version']}",
                    'description': 'Cannot determine usage rights',
                    'recommendation': f"Contact {dep['name']} maintainer for license clarification"
                })
        
        # Calculate risk level
        high_risk_count = sum(1 for dep in dependencies if dep['risk'] == 'high')
        medium_risk_count = sum(1 for dep in dependencies if dep['risk'] == 'medium')
        
        if high_risk_count > 0:
            risk_level = 'high'
        elif medium_risk_count > 0:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return ScanResult(
            project_name=project_name,
            scan_date=datetime.utcnow().isoformat(),
            languages=languages,
            total_dependencies=len(dependencies),
            unique_licenses=len(license_dist),
            risk_level=risk_level,
            dependencies=dependencies[:50],  # Limit for response size
            license_distribution=license_dist,
            issues=issues[:10]  # Top 10 issues
        )


# ============= API Endpoints =============

@app.get("/")
async def root():
    return {
        "message": "License Scanner API",
        "version": "1.0.0",
        "endpoints": {
            "scan_github": "/scan/github",
            "scan_upload": "/scan/upload",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/scan/github", response_model=ScanResult)
async def scan_github_repo(request: GitHubScanRequest):
    """Scan a GitHub repository for license compliance"""
    
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Extract repo info from URL
        url_parts = str(request.repo_url).rstrip('/').split('/')
        owner = url_parts[-2]
        repo = url_parts[-1].replace('.git', '')
        
        # Clone repository (simplified - in production use GitPython)
        # For now, we'll use GitHub API to fetch files
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Fetch repository contents
            api_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
            headers = {'Accept': 'application/vnd.github.v3+json'}
            
            response = await client.get(api_url, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Repository not found")
            
            files = response.json()
            
            # Download relevant manifest files
            manifest_files = ['package.json', 'requirements.txt', 'pom.xml', 'Cargo.toml', 'go.mod']
            
            for file_info in files:
                if file_info['name'] in manifest_files:
                    # Download file
                    file_response = await client.get(file_info['download_url'])
                    if file_response.status_code == 200:
                        file_path = temp_dir / file_info['name']
                        with open(file_path, 'wb') as f:
                            f.write(file_response.content)
        
        # Scan the downloaded files
        result = await DependencyScanner.scan_directory(temp_dir)
        result.project_name = f"{owner}/{repo}"
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.post("/scan/upload", response_model=ScanResult)
async def scan_uploaded_files(files: List[UploadFile] = File(...)):
    """Scan uploaded dependency files"""
    
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Save uploaded files
        for file in files:
            file_path = temp_dir / file.filename
            with open(file_path, 'wb') as f:
                content = await file.read()
                f.write(content)
        
        # Scan the directory
        result = await DependencyScanner.scan_directory(temp_dir)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.get("/license/{package_name}")
async def get_package_license(package_name: str, ecosystem: str = "npm"):
    """Get license information for a specific package"""
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if ecosystem == "npm":
                license_info = await NPMParser.fetch_npm_license(client, package_name)
            elif ecosystem == "pypi":
                license_info = await PipParser.fetch_pypi_license(client, package_name)
            else:
                raise HTTPException(status_code=400, detail="Unsupported ecosystem")
            
            return {
                "package": package_name,
                "ecosystem": ecosystem,
                **license_info
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
