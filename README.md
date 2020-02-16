![](https://bitbucket.org/surroundbitbucket/cheka/raw/master/style/cheka.png)

# CHEKA
A profile hierarchy-based RDF graph validation tool written in Python

This tool validates a data graph against a set of SHACL shape graphs that it extracts from a hierachy of Profiles (and 
Standards). It uses the claimed conformance of data in the data graph to a Profile to collate and then use all the 
validator SHACL files within the hierarchy of other Profiles and Standards which that Profile profiles.

Cheka uses [Profiles Vocabulary (PROF)](https://www.w3.org/TR/dx-prof/) descriptions of Profiles and Standards and both 
traverses up a Profile hierarchy (following `prof:isProfileOf` properties) and across from `prof:Profiles`s to 
`prof:ResourceDescriptors` that describe the constraints implemented for them. These constraints are currently limited 
to [Shapes Constraint Language (SHACL)](https://www.w3.org/TR/shacl/) files and must have the `prof:Role` of 
`role:validation` to be recognised by Cheka. The [pySHACL](https://github.com/RDFLib/pySHACL) Python SHACL validator is 
used to perform SHACL validation.


## Installation
1. Ensure Python 3 in enabled on your system
2. install requirements in *requirements.txt*, e.g. `~$ pip3 install -r requirements.txt`
3. Execute scripts as per *Use* below


## Use
### Input requirements
To use Cheka, you must supply it with both a data graph to be validated and a profiles hierarchy. It will then use 
conformance claims in the data graph to validate objects within it using validating resources it locates using the 
profiles hierarchy.


#### Data graph
This must be an RDF file with the part(s) to be validated indicating their conformance to a *profile* as per the 
Profiles Vocabulary.

Typically this will look like this:

```
@prefix dct: <http://purl.org/dc/terms/> .

<Object_X>
    a <Class_Y> ;
    dct:conformsTo <Profile_Z> ;
    ...
```

This says that `<Object_X>` is meant to conform to `<Profile_Z>`.

See the `tests/` folder for example data graphs.


### Profiles hierarchy
This must also be an RDF file that contains a hierarchy of `prof:Profile` objects (including `dct:Standard` objects) 
that are related to one another via the `prof:isProfileOf` property and each of which has a validating resource 
indicated by relating it to a `prof:Profile` via a `prof:ResourceDescriptor` like this:

```
@prefix dct: <http://purl.org/dc/terms/> .
@prefix prof: <http://www.w3.org/ns/dx/prof/> .
@prefix role:  <http://www.w3.org/ns/dx/prof/role/> .


<Standard_A>
    a dct:Standard ;
    prof:hasResource [
        a prof:ResourceDescriptor ;
        prof:hasRole role:validation ;
        prof:hasArtifact <File_or_Uri_J> ;
    ]
.

<Profile_B>
    a prof:Profile ;
    prof:isProfileOf <Standard_A> ;
    prof:hasResource <Resource_Descriptor_P> ;
.   

<Resource_Descriptor_P>
    a prof:ResourceDescriptor ;
    prof:hasRole role:validation ;
    prof:hasArtifact <File_or_Uri_K> ;
.

<Profile_C>
    a prof:Profile ; 
    prof:isProfileOf <Profile_B> ;    
    prof:hasResource [
        a prof:ResourceDescriptor ;
        prof:hasRole role:validation ;
        prof:hasArtifact <File_or_Uri_L> ;
    ] ;
.
```

This says `<Profile_C>` is a profile of `<Profile_B>` which is, in turn, a profile of `<Standard_A>`. The two profiles 
and the standard have resources `<File_or_Uri_J>`, `<File_or_Uri_K>` & `<File_or_Uri_L>` respectively which are 
indicated to be validators by the `prof:ResourceDescriptor` classes that associate them with their profiles/standard.

See the `tests/` folder for example profiles graphs.


### Running
Cheka uses the profiles graph to find all the SHACL validators it needs to validate a data graph. It returns a pySHACL 
result of [conforms, results_graph, results_text] with *conforms* being either True or False.

#### As a Python command line utility
```
~$ python3 cli.py -d DATA-GRAPH-FILE -p PROFILES-GRAPH-FILE
```
* `DATA-GRAPH-FILE` - The data graph, an RDF file, which is being validated
* `PROFILES-GRAPH-FILE` - The profiles hierarchy, an RDF file, that relates the Profiles and Standards for which you 
want to extract validating Profile Resources

If you make the cli.py script executable (`sudo chmod a+x cli.py`) then you can run it like this:

```
~$ ./cli.py -d DATA-GRAPH-FILE -p PROFILES-GRAPH-FILE
```


#### As a BASH script
The file `cheka` in the `bin/` drirectory is a BASH shell script that calls `cli.py`. Make it executable 
(`sudo chmod a+x cheka`) then you can run it like this:

```
~$ ./cheka -d DATA-GRAPH-FILE -p PROFILES-GRAPH-FILE
```


#### As a Windows executable
*coming!*


## Testing
Tests are included in the `tests/` directory. They should be able to be run from the Python command line and they have 
no dependencies, other than Cheka itself.  