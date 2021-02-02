# Jizici Bot（a.k.a. 夕立仿制机）

继承 Jizici 群里的原 Bot“夕立原型机”的功能，用（肯定不是）最小化的代码做到报时和怼人的功能。

## Licence

GLWTPL

### 为什么不用 AGPL？

Bot 界似乎普遍都在 **强制性** 地使用 AGPL，因为现存的 QQ Bot 实现有很多都是以 AGPL 许可证发布。

如果一个项目的代码依赖于上游的 (A)GPL 项目，那么它开源是完全正确且必须的。但是如果一个客户端软件调用了使用 (A)GPL 许可证的服务器端软件的网络 API，那么这个软件并无必要使用 (A)GPL 许可证，甚至不需要开源。

这里我的 Bot 调用了 CQHTTP API（现为 OneBot API）。我使用的实现是 [go-cqhttp](https://github.com/Mrs4s/go-cqhttp)，使用 AGPL 许可证开源。但是因为我只调用它的 HTTP API，所以我的代码并不需要同样使用 AGPL 许可证。

当然这并不意味着我鼓励 Bot 不开源。我只是希望说明一下我为什么把这个 Bot 用这个奇奇怪怪的许可证开放出来，顺便纠正一些误解 :)

Ref: https://opensource.stackexchange.com/a/4086
