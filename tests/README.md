# Testing README

## CLI options coverage
**Input**       | **Inputs***           | **Resources**                 | **Tests**
---             | ---                   | ---                           | ---
*data*          | one instance          | data/01.ttl (invalid)         | test_01
&nbsp;          | &nbsp;                | data/06.ttl (valid)           | test_01
&nbsp;          | multiple instances    | data/02.ttl                   | &nbsp;
&nbsp;          | subclasses            | data/03.ttl                   | &nbsp;
*profiles*      | none                  | -                             | &nbsp; 
&nbsp;          | one                   | profiles/01.ttl               | test_01
&nbsp;          | multiple, un-related  | profiles/02.ttl               | test_01
&nbsp;          | multiple, related     | profiles/03.ttl               | test_02  
*strategy*      | shacl                 | data/01.ttl & data/05.ttl     | test_03
&nbsp;          | &nbsp;                | profiles/03.ttl               | &nbsp;
&nbsp;          | profile               | data/01.ttl & data/04.ttl     | test_03
&nbsp;          | &nbsp;                | profiles/03.ttl               | test_04 
&nbsp;          | claims                | &nbsp;                        | **TODO**
*profile-uri*   | none                  | &nbsp;                        | test_01
&nbsp;          | uri                   | data/06.ttl (invalid)         | &nbsp; 
&nbsp;          | &nbsp;                | data/05.ttl (valid)           | &nbsp; 
&nbsp;          | &nbsp;                | profiles/03.ttl               | &nbsp; 
&nbsp;          | &nbsp;                | <http://example.org/profile/Profile_B> | &nbsp; 
&nbsp;          | &nbsp;                | <http://example.org/profile/Profile_C> | &nbsp; 
&nbsp;          | broken uri            | data/04.ttl                   | &nbsp; 
&nbsp;          | &nbsp;                | profiles/03.ttl               | &nbsp; 
&nbsp;          | &nbsp;                | <https://example.com/broken>  | &nbsp; 
*get-remotes*   | false                 | profiles/04.ttl               | test_05 
&nbsp;          | &nbsp;                | data/06.ttl                   | &nbsp;
&nbsp;          | true                  | profiles/04.ttl               | test_05 
&nbsp;          | &nbsp;                | data/06.ttl (invalid)         | &nbsp; 
&nbsp;          | &nbsp;                | data/05.ttl (valid)           | &nbsp; 
&nbsp;          | &nbsp;                | <https://w3id.org/profile/chekatest> | &nbsp; 



