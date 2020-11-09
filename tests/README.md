# Testing README

## CLI options coverage
**Input**       | **Inputs***           | **Resources**                 | **Tests**
---             | ---                   | ---                           | ---
*data*          | one instance          | data/01.ttl                   | &nbsp;
&nbsp;          | multiple instances    | data/02.ttl                   | &nbsp;
&nbsp;          | subclasses            | data/03.ttl                   | &nbsp;
*profiles*      | none                  | -                             | &nbsp; 
&nbsp;          | one                   | profiles/01.ttl               | &nbsp;
&nbsp;          | multiple, un-related  | profiles/02.ttl               | &nbsp;
&nbsp;          | multiple, related     | profiles/03.ttl               | &nbsp;  
*strategy*      | shacl                 | data/01.ttl & data/04.ttl     | &nbsp; 
&nbsp;          | &nbsp;                | validators/dataset-title.ttl  | &nbsp; 
&nbsp;          | profile               | data/01.ttl & data/04.ttl     | &nbsp; 
&nbsp;          | &nbsp;                | profiles/03.ttl               | &nbsp; 
&nbsp;          | claims                | &nbsp;                        | &nbsp; 
*profile-uri*   | none                  | &nbsp;                        | &nbsp; 
&nbsp;          | uri                   | data/04.ttl                   | &nbsp; 
&nbsp;          | &nbsp;                | profiles/03.ttl               | &nbsp; 
&nbsp;          | &nbsp;                | <http://example.org/profile/Profile_B> | &nbsp; 
&nbsp;          | &nbsp;                | <http://example.org/profile/Profile_C> | &nbsp; 
&nbsp;          | broken uri            | data/04.ttl                   | &nbsp; 
&nbsp;          | &nbsp;                | profiles/03.ttl               | &nbsp; 
&nbsp;          | &nbsp;                | <https://example.com/broken>  | &nbsp; 
*get-remotes*   | false                 | data/04.ttl                   | &nbsp; 
&nbsp;          | &nbsp;                | profiles/04.ttl               | &nbsp; 
&nbsp;          | true                  | data/04.ttl                   | &nbsp; 
&nbsp;          | &nbsp;                | profiles/04.ttl               | &nbsp; 
&nbsp;          | &nbsp;                | <https://w3id.org/profile/chekatest> | &nbsp; 



