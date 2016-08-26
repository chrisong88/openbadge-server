#OpenBadge API


##API Version 2.2: Multiple Endpoint meetings!
These docs are valid and at least partially tested against this commit


##Overview


All standard connections will start with a `GET` to `/projects`, and henceforth 
use the `projectKEY` returned by that request to communicate with the server, in the form of
`PUT`'s, `GET`'s, and `POST`'s to `/:projectKEY/[meetings|hubs|badges]`

There exist a collection of `God` level endpoints. These require a special key that will
not be available to any hubs meant for use by the end user. All other endpoints are restricted
to hubs that are members of the project being accessed. 

Every request should have an `X-APPKEY` header, or it will 401.
Endpoints accessible to project hubs should have an X-DEVICE-UUID header,
or they will error unauthorized. All request options are set through Headers.
The only instance where anything else is used is in POSTing data.  




##Endpoints
####Project Level Endpoints
Method                |        Path            | Summary                       | Accessible To
----------------------|------------------------|-------------------------------|------------------------------
[GET](#getproject)    | /projects              | get project's badges/members  | Project's Hubs

####Meeting Level Endpoints
Method                |        Path            | Summary                       | Accessible To
----------------------|------------------------|-------------------------------|------------------------------
[PUT](#putmeeting)    | /:projectID/meetings   | initialize a meeting          | Project's Hubs
[GET](#getmeeting)    | /:projectID/meetings   | get the meetings for a project| Project's Hubs
[POST](#postmeeting)  | /:projectID/meetings   | add data to a meeting        | Project's Hubs


####Hub Level Endpoints
Method                |        Path            | Summary                       | Accessible To
----------------------|------------------------|-------------------------------|------------------------------
[PUT](#puthub)        | /:anyNumber/hubs       | add hub to defualt project    | All    
[GET](#gethub)        | /:projectID/hubs       | get hub's metadata and projects| Project's Hubs











##Project Level Endpoints

<a name="getproject"></a>
###GET /projects

Get badge ownership info, project data, and hub data. 

**Headers Passed**

Key          | Type    |
-------------|---------|
X-HUB-UUID   | text    |

*Response Codes*
- 200 - got project info
- 404 - hub uuid not found

**Returned JSON**

```json
{
  "project": {
    "name": "Test Project 1",
    "key": "HAYFO5WZ6O",
    "members": {
      "C1:10:9A:32:E0:C4": {
        "name": "نادين",
        "key": "E0E2OQ79ZB"
      },
      "E3:26:AC:CD:0B:65": {
        "name": "Paul",
        "key": "3H7Y8SZ53Y"
      }
    },
    "active_meetings": [
      {
        "metadata": {
          "start_time": "1469492042.344",
          "history": {
            "postman": {
              "active_members": [
                "5LSA8S9VJX"
              ],
              "last_log_index": 2,
              "is_hub_active": true
            },
            "browser": {
              "active_members": [
                "ZGSMAUZ83D",
                "BEVA2BVBHH"
              ],
              "last_log_index": 4,
              "is_hub_active": true
            }
          },
          "uuid": "HAYFO5WZ6O|2414523523413.432",
          "end_time": null
        }
      }
    ],
  },
  "hub": {
    "last_updates": {
      "HAYFO5WZ6O|2414523523413.432": 4
    },
    "current_meeting": {
      "metadata": {
        "start_time": "1469492042.344",
        "history": {
          "active_members": [
            "ZGSMAUZ83D",
            "BEVA2BVBHH"
          ],
          "last_log_index": 4,
          "is_hub_active": true
        },
        "uuid": "HAYFO5WZ6O|2414523523413.432",
        "end_time": null
      }
    },
    "name": "My Computer",
    "su": false
  }
}
```




















##Meeting Level Endpoints


<a name="putmeeting"></a>
###PUT /:projectID/meetings

Create a meeting with given log version and uuid.

**Headers Passed**

Key          | Type    |
-------------|---------|
X-HUB-UUID   | text    |
X-LOG-VERSION| numeric |
X-MEETING-UUID|text|

*Response Codes*
- 200 - meeting created
- 401 - hub doesn't belong to project
- 404 - hubUUID not found
- 500 - meeting with that UUID likely already exists. or maybe malformed headers

**Returned JSON**

```json
{
  "details": "meeting created"
}
```




<a name="getmeeting"></a>
###GET /:projectID/meetings

Get all meetings in a project, with or without their respective files. 

If X-GET-FILES.lower() is equal to "true", this will return a UUID-accessible Associated Array of metadata and chunk
as separate entries in a dictionary. Otherwise, it will return a UUID-accessible Associated Array of metadata objects

**Headers Passed**

Key          | Type    |
-------------|---------|
X-HUB-UUID   | text    |
X-GET-FILES  | text    |


*Response Codes*
- 200 - got meetings
- 401 - hub doesn't belong to project
- 404 - hubUUID not found

**Returned JSON**

```json
{
  "meetings": {
    "HAYFO5WZ6O|2414523523413.432": {
      "events": [
        {
          "data": {},
          "log_timestamp": "1469492042.344",
          "type": "meeting started",
          "hub": "browser",
          "log_index": 0
        },
        {
          "data": {
            "hub_locale": "US/Eastern"
          },
          "log_timestamp": "1469492047.344",
          "type": "hub joined",
          "hub": "browser",
          "log_index": 1
        },
        {
          "data": {
            "hub_locale": "US/Eastern"
          },
          "log_timestamp": "1469492047.344",
          "type": "hub joined",
          "hub": "postman",
          "log_index": 0
        },
        {
          "data": {
            "key": "ZGSMAUZ83D",
            "address": "E3:09:E5:88:38:B2"
          },
          "log_timestamp": "1469492049.344",
          "type": "member joined",
          "hub": "browser",
          "log_index": 2
        },
        {
          "data": {
            "key": "5LSA8S9VJX",
            "address": "EA:B6:FF:F8:35:A3"
          },
          "log_timestamp": "1469492049.344",
          "type": "member joined",
          "hub": "postman",
          "log_index": 2
        },
        {
          "data": {
            "key": "BEVA2BVBHH",
            "address": "D2:3C:F6:B9:87:24"
          },
          "log_timestamp": "1469492057.344",
          "type": "member joined",
          "hub": "browser",
          "log_index": 3
        },
        {
          "data": {
            "timestamp": 1469492043.731,
            "sample_period": 50,
            "member": "ZGSMAUZ83D",
            "voltage": 2.75,
            "samples": [
              1,
              2,
              1,
              1,
              3,
              1,
              3,
              1,
              3
            ],
            "num_samples": 114,
            "badge_address": "E3:09:E5:88:38:B2"
          },
          "log_timestamp": "1469492059.344",
          "type": "audio received",
          "hub": "browser",
          "log_index": 4
        },
        {
          "data": {
            "timestamp": 1469492043.731,
            "sample_period": 50,
            "member": "ZGSMAUZ83D",
            "voltage": 2.75,
            "samples": [
              1,
              2,
              1,
              1,
              3,
              1,
              3,
              1,
              3
            ],
            "num_samples": 114,
            "badge_address": "E3:09:E5:88:38:B2"
          },
          "log_timestamp": "1469492059.344",
          "type": "audio received",
          "hub": "postman",
          "log_index": 1
        }
      ],
      "metadata": {
        "start_time": "1469492042.344",
        "end_time": null,
        "history": {
          "postman": {
            "active_members": [
              "5LSA8S9VJX"
            ],
            "last_log_index": 2,
            "is_hub_active": true
          },
          "browser": {
            "active_members": [
              "ZGSMAUZ83D",
              "BEVA2BVBHH"
            ],
            "last_log_index": 4,
            "is_hub_active": true
          }
        }
      }
    }
  }
}
```








<a name="postmeeting"></a>
###POST /:projectID/meetings

Add chunks to a meeting, tell us what chunks it has up until

**Headers Passed**

Key          | Type    |
-------------|---------|
X-HUB-UUID  | text    |
X-MEETING-UUID| text|

**Passed JSON**
```json
events:[
{
"type": "member joined",
"log_timestamp": 1469492049.344,
"log_index": 2,
"data":
    {"address":"E3:09:E5:88:38:B2","key":"ZGSMAUZ83D"}
 },
{
"type": "member joined",
"log_timestamp": 1469492057.344,
"log_index": 3,
"data": 
    {"address":"D2:3C:F6:B9:87:24","key":"BEVA2BVBHH"}
}
]
```

*Response Codes*
- 200 - chunks added


**Returned JSON**

```json
{
  "status": "success",
  "last_update_index": 4
}
```


















##Hub Level Endpoints

<a name="puthub"></a>
###PUT /0/hubs

Create a new hub in a default project, or rename a hub that already exists

**Headers Passed**

Key          | Type    |
-------------|---------|
X-APP-UUID   | text    |
X-HUB-UUID   | text    |
X-HUB-NAME   | text    |


*Response Codes*
- 200 - hub created


**Returned JSON**

```json
{
  "status": "added hub to default project",
}
```

```json
{
  "status": "renamed hub",
}
```


<a name="gethub"></a>
###GET /:projectID/hubs

Get hub's name and meetings, with all members added since given timestamp, its super user status, and its history object for the 
current meeting

**Headers Passed**

Key          | Type    |
-------------|---------|
X-HUB-UUID   | text    |
X-LAST-UPDATE| POSIX   |


*Response Codes*
- 200 - got hub data
- 401 - hub doesn't belong to project
- 404 - hubUUID not found

**Returned JSON**

```json
{
  "meeting": {
    "start_time": "1469492042.344",
    "history": {
      "active_members": [
        "ZGSMAUZ83D",
        "BEVA2BVBHH"
      ],
      "last_log_index": 4,
      "is_hub_active": true
    },
    "uuid": "HAYFO5WZ6O|2414523523413.432",
    "end_time": null
  },
  "su": false,
  "badge_map": {
    "C1:10:9A:32:E0:C4": {
      "name": "نادين",
      "key": "E0E2OQ79ZB"
    },
    "E3:26:AC:CD:0B:65": {
      "name": "Paul",
      "key": "3H7Y8SZ53Y"
    }
}
```

















































##Documentation Format
####(courtesy of [Conner DiPaolo](https://github.com/cdipaolo))

Keep documentation in this format please!

Add the method to the [path overview](#paths) and place it under the correct [section](#sections)

```markdown
<a name="briefname"></a>
###METHOD /path/to/endpoint

put a decent description of what the endpoint does here

**Headers Passed**

Key   | Type    | Description
------|---------|------------
key   | string  | here's a header description

**Passed JSON**
{
  "example":"of",
  "passed":"json",
  "goes":{
    "here":true
  }
}


*Response Codes*
- 400 - invalid request
- 200 - OK
- 201 - thing was created
- 401 - unauthorized

**Returned JSON**
{
  "example":"of",
  "return":"json",
  "goes":{
    "here":true
  }
}

#####Comments

put notes here about, for example, optional parameters and/or specific types

```