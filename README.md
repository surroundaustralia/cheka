![](https://bitbucket.org/surroundbitbucket/cheka/raw/master/style/cheka.png)

# CHEKA
A profile hierarchy-based RDF graph validation tool written in Python

This tool validates a data graph against a set of SHACL shape graphs that it extracts from a hierachy of Profiles (and Standards). It uses the claimed conformance of data in the data graph to a Profile to collate and then use all the validator SHACL files within the hierarchy of other Profiles and Standards which that Profile profiles.

Cheka uses [Profiles Vocabulary (PROF)](https://www.w3.org/TR/dx-prof/) descriptions of Profiles and Standards and both traverses up a Profile hierarchy (following `prof:isProfileOf` properties) and across from `prof:Profiles`s to `prof:ResourceDescriptors` that describe the constraints implemented for them. These constraints are currently limited to [Shapes Constraint Language (SHACL)](https://www.w3.org/TR/shacl/) files and must have the `prof:Role` of `role:validation` to be recognised by Cheka. The [pySHACL](https://github.com/RDFLib/pySHACL) Python SHACL validator is used to perform SHACL validation.


## Installation
*coming!*


## Use
### Input requirements
To use Cheka, you must supply it with both a data graph to be validated and a profiles hierarchy. It will then use conformance claims in the data graph to validate objects within it using validating resources it locates using the profiles hairarchy.


#### Data graph
This must be an RDF file with the part(s) to be validated indicating their conformance to a *profile* as per the Profiles Vocabulary.

Typically this will look like this:

```
@prefix dct: <http://purl.org/dc/terms/> .

<Object_X>
    a <Class_Y> ;
    dct:conformsTo <Profile_Z> ;
    ...
```

This says that `<Object_X>` is meant to conform to `<Profile_Z>`.

See the `examples/` folder for example data graphs.


### Profiles hierarchy
This must also be an RDF file that contains a hierarchy of `prof:Profile` objects (including `dct:Standard` objects) that are related to one another via the `prof:isProfileOf` property and each of which has a validating resource indicated by relating it to a `prof:Profile` via a `prof:ResourceDescriptor` like this:

```
@prefix dct: <http://purl.org/dc/terms/> .
@prefix prof: <http://www.w3.org/ns/dx/prof/> .
@prefix role:  <http://www.w3.org/ns/dx/prof/role/> .

<Standard_A>
    a dct:Standard ;
    prof:hasResource [
        a prof:ResourceDescriptor ;
        prof:hasRole role:validation .
        prof:hasArtifact <File_or_Uri_J> ;
    ]
    ...

<Profile_B>
    a prof:Profile ;
    prof:isProfileOf <Standard_A> ;
    prof:hasResource <Resource_Descriptor_P> ;
    ...    

<Resource_Descriptor_P> ;
    a prof:ResourceDescriptor ;
    prof:hasRole role:validation .
    prof:hasArtifact <File_or_Uri_K> ;
.

<Profile_C>
    a prof:Profile ; 
    prof:isProfileOf <Profile_B> ;    
    prof:hasResource [
        a prof:ResourceDescriptor ;
        prof:hasRole role:validation .
        prof:hasArtifact <File_or_Uri_L> ;
    ]
    ...
```

This says `<Profile_C>` is a profile of `<Profile_B>` which is, in turn, a profile of `<Standard_A>`. The two profiles and the standard have resources `<File_or_Uri_J>`, `<File_or_Uri_K>` & `<File_or_Uri_L>` respectively which are indicated to be validators by the `prof:ResourceDescriptor` classes that associate them with their profiles/standard.



### Running
#### As a Python command line utility
```
~$ python3 cheka.py -d DATAGRAPH -p PROFILES-HIERARCHY
```
* `DATAGRAPH` - The data graph, an RDF file, which is being validated
* `PROFILES-HIERARCHY` - the Profiles Vocabulary hierarchy, an RDF file, that relates the Profiles and Standards for which you want to extract validating Profile Resources

If you make the cheka.py script executable (`sudo chmod a+x cheka.py`) then you can run it like this:

```
~$ ./cheka.py -d DATAGRAPH -p PROFILES-HIERARCHY
```


#### As a BASH script
The file `cheka` in the `bin/` drirectory is a BASH shell script that calls `cheka.py`. Make it executable (`sudo chmod a+x cheka`) then you can run it like this:

```
~$ ./cheka -d DATAGRAPH -p PROFILES-HIERARCHY
```


#### As a Windows executable
*coming!*
